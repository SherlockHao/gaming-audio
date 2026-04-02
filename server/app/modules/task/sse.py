import asyncio
import uuid
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from app.core.deps import DBSession
from app.core.models import Task

router = APIRouter(tags=["sse"])

async def task_status_generator(task_id: uuid.UUID, db_factory):
    """Generate SSE events when task status changes."""
    last_status = None
    while True:
        try:
            async with db_factory() as session:
                result = await session.execute(
                    select(Task.status, Task.updated_at).where(Task.task_id == task_id)
                )
                row = result.one_or_none()
                if not row:
                    yield {"event": "error", "data": "Task not found"}
                    return

                current_status, updated_at = row
                if current_status != last_status:
                    last_status = current_status
                    yield {
                        "event": "status_change",
                        "data": f'{{"task_id": "{task_id}", "status": "{current_status}", "updated_at": "{updated_at.isoformat()}"}}',
                    }

                # Terminal states — stop streaming
                if current_status in ("Approved", "Rejected", "RolledBack"):
                    return

        except Exception:
            pass

        await asyncio.sleep(2)  # Poll every 2 seconds


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: uuid.UUID):
    from app.database import async_session_factory
    return EventSourceResponse(task_status_generator(task_id, async_session_factory))
