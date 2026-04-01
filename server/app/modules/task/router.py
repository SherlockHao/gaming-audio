import uuid
from fastapi import APIRouter, HTTPException, Query
from app.core.deps import DBSession
from app.core.schemas import ProjectCreate, ProjectOut, TaskCreate, TaskListOut, TaskOut, TaskUpdate
from app.modules.task.service import ProjectService, TaskService

router = APIRouter(tags=["tasks"])

@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate, db: DBSession):
    svc = ProjectService(db)
    return await svc.create_project(data)

@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(db: DBSession):
    svc = ProjectService(db)
    return await svc.list_projects()

@router.post("/tasks", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.create_task(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return task

@router.get("/tasks", response_model=TaskListOut)
async def list_tasks(db: DBSession, project_id: uuid.UUID | None = None, status: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    svc = TaskService(db)
    tasks, total = await svc.list_tasks(project_id=project_id, status=status, offset=offset, limit=limit)
    return TaskListOut(items=tasks, total=total)

@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: uuid.UUID, db: DBSession):
    svc = TaskService(db)
    task = await svc.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def update_task(task_id: uuid.UUID, data: TaskUpdate, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.update_task(task_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/tasks/{task_id}/submit", response_model=TaskOut)
async def submit_task(task_id: uuid.UUID, db: DBSession):
    svc = TaskService(db)
    try:
        task = await svc.submit_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
