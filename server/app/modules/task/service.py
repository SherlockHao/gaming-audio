import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Project, Task
from app.core.schemas import VALID_ASSET_TYPES, VALID_PLAY_MODES, ProjectCreate, TaskCreate, TaskUpdate

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(self, data: ProjectCreate) -> Project:
        project = Project(name=data.name)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def list_projects(self) -> list[Project]:
        result = await self.db.execute(select(Project))
        return list(result.scalars().all())

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, data: TaskCreate) -> Task:
        if data.asset_type not in VALID_ASSET_TYPES:
            raise ValueError(f"Invalid asset_type: {data.asset_type}. Must be one of {VALID_ASSET_TYPES}")
        if data.play_mode not in VALID_PLAY_MODES:
            raise ValueError(f"Invalid play_mode: {data.play_mode}. Must be one of {VALID_PLAY_MODES}")
        task = Task(
            project_id=data.project_id,
            title=data.title,
            requester=data.requester,
            asset_type=data.asset_type,
            semantic_scene=data.semantic_scene,
            play_mode=data.play_mode,
            tags=data.tags,
            notes=data.notes,
            priority=data.priority,
            status="Draft",
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> Task | None:
        result = await self.db.execute(select(Task).where(Task.task_id == task_id))
        return result.scalar_one_or_none()

    async def list_tasks(self, project_id: uuid.UUID | None = None, status: str | None = None, offset: int = 0, limit: int = 20) -> tuple[list[Task], int]:
        query = select(Task)
        count_query = select(func.count()).select_from(Task)
        if project_id:
            query = query.where(Task.project_id == project_id)
            count_query = count_query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        tasks = list(result.scalars().all())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        return tasks, total

    async def update_task(self, task_id: uuid.UUID, data: TaskUpdate) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status != "Draft":
            raise ValueError("Can only edit tasks in Draft status")
        update_data = data.model_dump(exclude_unset=True)
        if "asset_type" in update_data and update_data["asset_type"] not in VALID_ASSET_TYPES:
            raise ValueError(f"Invalid asset_type: {update_data['asset_type']}")
        if "play_mode" in update_data and update_data["play_mode"] not in VALID_PLAY_MODES:
            raise ValueError(f"Invalid play_mode: {update_data['play_mode']}")
        for key, value in update_data.items():
            setattr(task, key, value)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def submit_task(self, task_id: uuid.UUID) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None
        if task.status != "Draft":
            raise ValueError("Can only submit tasks in Draft status")
        task.status = "Submitted"
        await self.db.commit()
        await self.db.refresh(task)
        return task
