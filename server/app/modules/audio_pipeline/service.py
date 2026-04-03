"""Audio pipeline service: generates candidates, stores them, transitions task state."""
import os
import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import AudioIntentSpec, CandidateAudio, Task, Project, CategoryRule
from app.core.storage import upload_file
from app.modules.audio_pipeline.prompt import build_audio_prompt
from app.modules.audio_pipeline.generator import generate_audio_candidates
from app.modules.audit.service import AuditService

logger = logging.getLogger(__name__)


class AudioPipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = AuditService(db)

    async def generate_candidates(self, task_id: uuid.UUID) -> list[CandidateAudio]:
        """Generate audio candidates for a task.

        Task must be in SpecGenerated state with an AudioIntentSpec.
        """
        # Load task
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        if task.status != "SpecGenerated":
            raise ValueError(f"Task must be in SpecGenerated status, currently: {task.status}")

        # Load intent spec
        spec_result = await self.db.execute(
            select(AudioIntentSpec).where(AudioIntentSpec.task_id == task_id)
        )
        spec = spec_result.scalar_one_or_none()
        if not spec:
            raise ValueError("No AudioIntentSpec found for this task")

        # Load project for style bible
        proj_result = await self.db.execute(
            select(Project).where(Project.project_id == task.project_id)
        )
        project = proj_result.scalar_one_or_none()
        style_bible = project.style_bible if project else None

        # Load category rule
        cat_rule_body = None
        if spec.category_rule_id:
            rule_result = await self.db.execute(
                select(CategoryRule).where(CategoryRule.rule_id == spec.category_rule_id)
            )
            rule = rule_result.scalar_one_or_none()
            if rule:
                cat_rule_body = rule.rule_body

        # Build prompt
        spec_dict = {
            "content_type": spec.content_type,
            "semantic_role": spec.semantic_role,
            "intensity": spec.intensity,
            "material_hint": spec.material_hint,
            "loop_required": spec.loop_required,
        }
        prompt = build_audio_prompt(spec_dict, style_bible, cat_rule_body)

        # Determine duration from category rule
        duration_ms = 1000
        if cat_rule_body:
            dur = cat_rule_body.get("duration", {})
            duration_ms = dur.get("max_ms", 1000) // 2  # Use midpoint

        # Generate candidates
        raw_candidates = await generate_audio_candidates(
            prompt=prompt,
            count=spec.variation_count or 3,
            duration_ms=duration_ms,
        )

        if not raw_candidates:
            # Transition to failed
            from app.modules.task.service import TaskService
            task_svc = TaskService(self.db)
            await task_svc._transition(task, "audio_fail", actor="system:audio_pipeline")
            await self._audit.log(
                actor="system:audio_pipeline", action="audio_generation_failed",
                task_id=task_id, project_id=task.project_id,
                error_context={"reason": "No candidates produced"},
            )
            await self.db.commit()
            raise ValueError("Audio generation failed: no candidates produced")

        # Store candidates in MinIO and create DB records
        candidates = []
        for i, raw in enumerate(raw_candidates):
            local_path = raw["file_path"]
            object_name = f"{task.project_id}/{task_id}/candidates/candidate_{i:02d}.wav"

            try:
                stored_path = await upload_file(local_path, object_name, "audio/wav")
            except Exception as e:
                logger.warning(f"Failed to upload candidate {i}: {e}")
                stored_path = object_name  # Fallback: store the intended path

            candidate = CandidateAudio(
                task_id=task_id,
                version=1,
                source_model=raw.get("source_model", "unknown"),
                generation_params=raw.get("generation_params"),
                file_path=stored_path,
                duration_ms=raw.get("duration_ms"),
                stage="source",
                selected=(i == 0),  # First candidate auto-selected
            )
            self.db.add(candidate)
            candidates.append(candidate)

            # Clean up temp file
            try:
                if os.path.exists(local_path):
                    os.unlink(local_path)
            except OSError:
                pass

        await self.db.commit()
        for c in candidates:
            await self.db.refresh(c)

        # Transition task to AudioGenerated
        from app.modules.task.service import TaskService
        task_svc = TaskService(self.db)
        await task_svc._transition(task, "audio_ok", actor="system:audio_pipeline")

        # Audit log
        await self._audit.log(
            actor="system:audio_pipeline",
            action="audio_generated",
            task_id=task_id,
            project_id=task.project_id,
            detail={"candidate_count": len(candidates), "prompt_length": len(prompt)},
        )
        await self.db.commit()

        return candidates

    async def get_candidates(self, task_id: uuid.UUID) -> list[CandidateAudio]:
        result = await self.db.execute(
            select(CandidateAudio)
            .where(CandidateAudio.task_id == task_id)
            .order_by(CandidateAudio.version, CandidateAudio.candidate_id)
        )
        return list(result.scalars().all())

    async def select_candidate(self, task_id: uuid.UUID, candidate_id: uuid.UUID) -> CandidateAudio | None:
        """Mark a candidate as selected (deselect others)."""
        candidates = await self.get_candidates(task_id)
        selected = None
        for c in candidates:
            if c.candidate_id == candidate_id:
                c.selected = True
                selected = c
            else:
                c.selected = False
        if selected:
            await self.db.commit()
            await self.db.refresh(selected)
        return selected
