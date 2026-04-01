import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import AuditLog

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, actor: str, action: str, task_id: uuid.UUID | None = None, project_id: uuid.UUID | None = None, old_state: str | None = None, new_state: str | None = None, detail: dict | None = None, error_context: dict | None = None) -> AuditLog:
        entry = AuditLog(task_id=task_id, project_id=project_id, actor=actor, action=action, old_state=old_state, new_state=new_state, detail=detail, error_context=error_context)
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_task_logs(self, task_id: uuid.UUID, limit: int = 50) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.task_id == task_id).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
