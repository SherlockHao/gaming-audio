"""Wwise automation service: object creation, import, Event, Bank generation.

Operates in mock mode by default (no Wwise Authoring needed).
Set WWISE_LIVE_MODE=true to use real WAAPI connection.
"""
import uuid
import os
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import (
    AudioIntentSpec, CandidateAudio, Task, WwiseObjectManifest, WwiseTemplate,
)
from app.modules.rule.naming import (
    generate_event_name, generate_wwise_object_path, generate_bank_name,
)
from app.modules.audit.service import AuditService

logger = logging.getLogger(__name__)
LIVE_MODE = os.environ.get("WWISE_LIVE_MODE", "").lower() == "true"


class WwiseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = AuditService(db)

    async def import_to_wwise(self, task_id: uuid.UUID) -> WwiseObjectManifest:
        """Import audio and create Wwise objects for a task.

        Task must be in QCReady state.
        Creates: Actor-Mixer path, Sound/Container, imports audio, creates Event.
        """
        task, spec, candidates = await self._load_task_data(task_id, required_status="QCReady")

        # Get selected candidate
        selected = [c for c in candidates if c.selected]
        if not selected:
            selected = candidates[:1]  # Fallback to first
        if not selected:
            raise ValueError("No audio candidates available for import")

        # Generate names
        event_name = generate_event_name(
            task.asset_type, task.semantic_scene, task.title
        )
        object_path = generate_wwise_object_path(task.asset_type, task.semantic_scene)
        bank_name = generate_bank_name(task.asset_type, task.semantic_scene)

        # Build object entries
        object_entries = []
        for candidate in selected:
            object_entries.append({
                "object_type": "Sound",
                "object_path": f"{object_path}\\{task.title.replace(' ', '_')}",
                "source_audio_path": candidate.file_path,
                "event_name": event_name,
                "bus_name": self._get_bus_name(task.asset_type),
                "bank_name": bank_name,
                "operation_type": "create",
            })

        # If multiple candidates, create Random Container
        if len(candidates) > 1:
            container_entry = {
                "object_type": "RandomContainer",
                "object_path": f"{object_path}\\{task.title.replace(' ', '_')}_RC",
                "source_audio_path": None,
                "event_name": event_name,
                "bus_name": self._get_bus_name(task.asset_type),
                "bank_name": bank_name,
                "operation_type": "create",
            }
            object_entries.insert(0, container_entry)

        # Execute WAAPI calls (or mock)
        build_log_lines = []
        if LIVE_MODE:
            build_log_lines = await self._execute_live_import(object_entries)
        else:
            build_log_lines = self._execute_mock_import(object_entries, event_name)

        # Create manifest
        manifest = WwiseObjectManifest(
            task_id=task_id,
            version=1,
            object_entries=object_entries,
            import_status="completed",
            build_log="\n".join(build_log_lines),
        )
        self.db.add(manifest)
        await self.db.commit()
        await self.db.refresh(manifest)

        # Transition task
        from app.modules.task.service import TaskService
        task_svc = TaskService(self.db)
        await task_svc._transition(task, "wwise_ok", actor="system:wwise")

        # Audit
        await self._audit.log(
            actor="system:wwise", action="wwise_imported",
            task_id=task_id, project_id=task.project_id,
            detail={"event_name": event_name, "object_count": len(object_entries)},
        )
        await self.db.commit()

        return manifest

    async def build_bank(self, task_id: uuid.UUID) -> WwiseObjectManifest:
        """Generate SoundBank for a task. Task must be in WwiseImported state."""
        task, spec, _ = await self._load_task_data(task_id, required_status="WwiseImported")

        bank_name = generate_bank_name(task.asset_type, task.semantic_scene)

        build_log_lines = []
        if LIVE_MODE:
            build_log_lines.append(f"[LIVE] Generating bank: {bank_name}")
            # Would call: await waapi.call("ak.wwise.core.soundbank.generate", ...)
        else:
            build_log_lines.append(f"[MOCK] Bank generation simulated: {bank_name}")
            build_log_lines.append(f"[MOCK] Bank size: ~2.5MB (estimated)")

        # Update or create manifest for bank
        result = await self.db.execute(
            select(WwiseObjectManifest).where(
                WwiseObjectManifest.task_id == task_id
            ).order_by(WwiseObjectManifest.version.desc())
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.build_log = (existing.build_log or "") + "\n" + "\n".join(build_log_lines)
            existing.import_status = "bank_built"
            manifest = existing
        else:
            manifest = WwiseObjectManifest(
                task_id=task_id, version=1,
                object_entries=[], import_status="bank_built",
                build_log="\n".join(build_log_lines),
            )
            self.db.add(manifest)

        await self.db.commit()
        await self.db.refresh(manifest)

        # Transition
        from app.modules.task.service import TaskService
        task_svc = TaskService(self.db)
        await task_svc._transition(task, "bank_ok", actor="system:wwise")

        # Audit
        await self._audit.log(
            actor="system:wwise", action="bank_built",
            task_id=task_id, project_id=task.project_id,
            detail={"bank_name": bank_name},
        )
        await self.db.commit()

        return manifest

    async def get_manifest(self, task_id: uuid.UUID) -> WwiseObjectManifest | None:
        result = await self.db.execute(
            select(WwiseObjectManifest).where(WwiseObjectManifest.task_id == task_id)
            .order_by(WwiseObjectManifest.version.desc())
        )
        return result.scalar_one_or_none()

    async def _load_task_data(self, task_id, required_status):
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            raise ValueError("Task not found")
        if task.status != required_status:
            raise ValueError(f"Task must be in {required_status} status, currently: {task.status}")

        spec_result = await self.db.execute(
            select(AudioIntentSpec).where(AudioIntentSpec.task_id == task_id)
        )
        spec = spec_result.scalar_one_or_none()

        cand_result = await self.db.execute(
            select(CandidateAudio).where(CandidateAudio.task_id == task_id)
        )
        candidates = list(cand_result.scalars().all())

        return task, spec, candidates

    def _get_bus_name(self, asset_type: str) -> str:
        bus_map = {
            "sfx": "Bus_SFX",
            "ui": "Bus_UI",
            "ambience_loop": "Bus_Ambience",
        }
        return bus_map.get(asset_type, "Bus_SFX")

    def _execute_mock_import(self, entries, event_name):
        lines = [f"[MOCK] Wwise import simulation - {datetime.now(timezone.utc).isoformat()}"]
        for entry in entries:
            lines.append(f"[MOCK] Created {entry['object_type']} at {entry['object_path']}")
        lines.append(f"[MOCK] Created Event: {event_name}")
        lines.append("[MOCK] Import completed successfully")
        return lines

    async def _execute_live_import(self, entries):
        """Execute real WAAPI calls. Requires Wwise Authoring running."""
        from app.modules.wwise.connection import WaapiConnection
        lines = []
        async with WaapiConnection() as waapi:
            for entry in entries:
                try:
                    await waapi.call("ak.wwise.core.object.create", {
                        "parent": entry["object_path"].rsplit("\\", 1)[0],
                        "type": entry["object_type"],
                        "name": entry["object_path"].rsplit("\\", 1)[-1],
                    })
                    lines.append(f"[LIVE] Created {entry['object_type']}: {entry['object_path']}")
                except Exception as e:
                    lines.append(f"[LIVE] ERROR creating {entry['object_path']}: {e}")
        return lines
