import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.deps import DBSession
from app.modules.wwise.service import WwiseService

router = APIRouter(tags=["wwise"])


class WwiseManifestOut(BaseModel):
    manifest_id: uuid.UUID
    task_id: uuid.UUID
    version: int
    object_entries: list[dict]
    import_status: str
    build_log: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


@router.post("/tasks/{task_id}/wwise/import", response_model=WwiseManifestOut, status_code=201)
async def import_to_wwise(task_id: uuid.UUID, db: DBSession):
    svc = WwiseService(db)
    try:
        manifest = await svc.import_to_wwise(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return manifest


@router.post("/tasks/{task_id}/wwise/build-bank", response_model=WwiseManifestOut)
async def build_bank(task_id: uuid.UUID, db: DBSession):
    svc = WwiseService(db)
    try:
        manifest = await svc.build_bank(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return manifest


@router.get("/tasks/{task_id}/wwise/manifest", response_model=WwiseManifestOut | None)
async def get_manifest(task_id: uuid.UUID, db: DBSession):
    svc = WwiseService(db)
    return await svc.get_manifest(task_id)
