import asyncio
import logging
import uuid
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from app.core.models import Task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sse"])

MAX_CONNECTION_SECONDS = 1800  # 30 minutes
POLL_INTERVAL = 2
HEARTBEAT_INTERVAL = 15  # Send ping every 15 seconds


async def task_status_generator(task_id: uuid.UUID, db_factory):
    last_status = None
    elapsed = 0
    heartbeat_counter = 0

    while elapsed < MAX_CONNECTION_SECONDS:
        try:
            async with db_factory() as session:
                result = await session.execute(
                    select(Task.status, Task.updated_at).where(Task.task_id == task_id)
                )
                row = result.one_or_none()
                if not row:
                    yield {"event": "error", "data": '{"error": "Task not found"}'}
                    return

                current_status, updated_at = row
                if current_status != last_status:
                    last_status = current_status
                    yield {
                        "event": "status_change",
                        "data": f'{{"task_id": "{task_id}", "status": "{current_status}", "updated_at": "{updated_at.isoformat()}"}}',
                    }

                if current_status in ("Approved", "Rejected", "RolledBack"):
                    return

        except Exception as e:
            logger.warning(f"SSE poll error for task {task_id}: {e}")

        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        heartbeat_counter += POLL_INTERVAL
        if heartbeat_counter >= HEARTBEAT_INTERVAL:
            heartbeat_counter = 0
            yield {"event": "ping", "data": ""}

    # Max time reached
    yield {"event": "timeout", "data": '{"message": "Connection timeout after 30 minutes"}'}


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: uuid.UUID):
    from app.database import async_session_factory
    return EventSourceResponse(task_status_generator(task_id, async_session_factory))
