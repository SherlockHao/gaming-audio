import uuid
from datetime import datetime
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.core.deps import DBSession
from app.modules.audit.service import AuditService

router = APIRouter(tags=["audit"])

class AuditLogOut(BaseModel):
    log_id: int
    task_id: uuid.UUID | None
    project_id: uuid.UUID | None
    actor: str
    action: str
    old_state: str | None
    new_state: str | None
    detail: dict | None
    error_context: dict | None
    created_at: datetime
    model_config = {"from_attributes": True}

@router.get("/tasks/{task_id}/audit-log", response_model=list[AuditLogOut])
async def get_task_audit_log(task_id: uuid.UUID, db: DBSession, limit: int = Query(50, ge=1, le=200)):
    svc = AuditService(db)
    logs = await svc.get_task_logs(task_id, limit)
    return logs
