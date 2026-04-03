"""QC service: runs quality checks on audio candidates."""
import uuid
import tempfile
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import AudioIntentSpec, CandidateAudio, CategoryRule, QcReport, Task
from app.modules.audio_pipeline.processor import analyze_audio_file, run_qc_checks
from app.core.storage import download_file
from app.modules.audit.service import AuditService
import logging

logger = logging.getLogger(__name__)


class QCService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = AuditService(db)

    async def run_qc(self, task_id: uuid.UUID) -> list[QcReport]:
        """Run QC on all candidates for a task.

        Task must be in AudioGenerated state.
        At least one candidate must pass for task to proceed.
        """
        # Load task
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        if task.status != "AudioGenerated":
            raise ValueError(f"Task must be in AudioGenerated status, currently: {task.status}")

        # Load spec for category rule reference
        spec_result = await self.db.execute(
            select(AudioIntentSpec).where(AudioIntentSpec.task_id == task_id)
        )
        spec = spec_result.scalar_one_or_none()

        # Load category rule
        cat_rule_body = None
        if spec and spec.category_rule_id:
            rule_result = await self.db.execute(
                select(CategoryRule).where(CategoryRule.rule_id == spec.category_rule_id)
            )
            rule = rule_result.scalar_one_or_none()
            if rule:
                cat_rule_body = rule.rule_body

        # Load candidates
        cand_result = await self.db.execute(
            select(CandidateAudio).where(CandidateAudio.task_id == task_id)
        )
        candidates = list(cand_result.scalars().all())
        if not candidates:
            raise ValueError("No candidates found for QC")

        reports = []
        passed_count = 0

        for candidate in candidates:
            # Try to analyze the actual file (download from MinIO if needed)
            analysis = await self._analyze_candidate(candidate)

            # Run QC checks
            qc_results = run_qc_checks(analysis, cat_rule_body)

            # Create QcReport
            report = QcReport(
                task_id=task_id,
                candidate_id=candidate.candidate_id,
                peak_result=qc_results.get("peak_result"),
                loudness_result=qc_results.get("loudness_result"),
                spectrum_result=qc_results.get("spectrum_result"),
                head_tail_result=qc_results.get("head_tail_result"),
                format_result=qc_results.get("format_result"),
                qc_status=qc_results["qc_status"],
            )
            self.db.add(report)
            reports.append(report)

            if qc_results["qc_status"] == "passed":
                passed_count += 1

        await self.db.commit()
        for r in reports:
            await self.db.refresh(r)

        # Transition task based on QC results
        from app.modules.task.service import TaskService
        task_svc = TaskService(self.db)
        if passed_count > 0:
            await task_svc._transition(task, "qc_pass", actor="system:qc")
        else:
            await task_svc._transition(task, "qc_fail", actor="system:qc")

        # Audit
        await self._audit.log(
            actor="system:qc", action="qc_completed",
            task_id=task_id, project_id=task.project_id,
            detail={"total_candidates": len(candidates), "passed": passed_count,
                    "failed": len(candidates) - passed_count},
        )
        await self.db.commit()

        return reports

    async def get_qc_reports(self, task_id: uuid.UUID) -> list[QcReport]:
        result = await self.db.execute(
            select(QcReport).where(QcReport.task_id == task_id)
        )
        return list(result.scalars().all())

    async def _analyze_candidate(self, candidate: CandidateAudio) -> dict:
        """Analyze a candidate's audio file. Downloads from MinIO if needed."""
        # For MVP/dev, try to analyze the file if it exists locally
        # In production, would download from MinIO first
        if os.path.exists(candidate.file_path):
            return analyze_audio_file(candidate.file_path)

        # Try downloading from MinIO
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            await download_file(candidate.file_path, tmp.name)
            analysis = analyze_audio_file(tmp.name)
            os.unlink(tmp.name)
            return analysis
        except Exception as e:
            logger.warning(f"Could not analyze candidate {candidate.candidate_id}: {e}")
            return {
                "sample_rate": 0, "bit_depth": 0, "channels": 0,
                "duration_ms": 0, "peak_dbfs": 0.0, "rms_dbfs": -96.0,
                "head_silence_ms": 0, "tail_silence_ms": 0,
                "error": str(e),
            }
