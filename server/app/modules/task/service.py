import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import InputAssetRef, Project, Task
from app.core.schemas import ProjectCreate, TaskCreate, TaskUpdate

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
        # Pydantic Literal types handle asset_type and play_mode validation
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
        from app.modules.audit.service import AuditService
        audit = AuditService(self.db)
        await audit.log(
            actor=task.requester,
            action="task_created",
            task_id=task.task_id,
            project_id=task.project_id,
            new_state="Draft",
            detail={"title": task.title, "asset_type": task.asset_type},
        )
        await self.db.commit()
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
        # Pydantic Literal types handle asset_type and play_mode validation
        for key, value in update_data.items():
            setattr(task, key, value)
        await self.db.commit()
        await self.db.refresh(task)

        # Audit log
        from app.modules.audit.service import AuditService
        audit = AuditService(self.db)
        await audit.log(
            actor="system", action="task_updated", task_id=task.task_id,
            project_id=task.project_id, detail={"updated_fields": list(update_data.keys())},
        )
        await self.db.commit()

        return task

    async def _transition(self, task: Task, trigger: str, actor: str = "system") -> Task:
        from app.core.state_machine import transition_task, InvalidTransition
        old_state = task.status
        try:
            new_state = transition_task(old_state, trigger)
        except InvalidTransition as e:
            raise ValueError(str(e))
        task.status = new_state
        from app.modules.audit.service import AuditService
        audit = AuditService(self.db)
        await audit.log(
            actor=actor,
            action=f"task_{trigger}",
            task_id=task.task_id,
            project_id=task.project_id,
            old_state=old_state,
            new_state=new_state,
        )
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def submit_task(self, task_id: uuid.UUID) -> Task | None:
        task = await self.get_task(task_id)
        if not task:
            return None

        # Check task has at least one input asset
        count_result = await self.db.execute(
            select(func.count()).select_from(InputAssetRef).where(InputAssetRef.task_id == task_id)
        )
        asset_count = count_result.scalar() or 0
        if asset_count == 0:
            raise ValueError("Cannot submit task without at least one input asset. Upload a file first.")

        return await self._transition(task, "submit", actor=task.requester)
