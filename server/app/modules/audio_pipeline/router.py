import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.deps import DBSession
from app.modules.audio_pipeline.service import AudioPipelineService

router = APIRouter(tags=["audio"])


class CandidateOut(BaseModel):
    candidate_id: uuid.UUID
    task_id: uuid.UUID
    version: int
    source_model: str | None
    generation_params: dict | None
    file_path: str
    duration_ms: int | None
    stage: str
    selected: bool
    created_at: datetime
    model_config = {"from_attributes": True}


@router.post("/tasks/{task_id}/audio/generate", response_model=list[CandidateOut], status_code=201)
async def generate_audio(task_id: uuid.UUID, db: DBSession):
    svc = AudioPipelineService(db)
    try:
        candidates = await svc.generate_candidates(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return candidates


@router.get("/tasks/{task_id}/audio/candidates", response_model=list[CandidateOut])
async def list_candidates(task_id: uuid.UUID, db: DBSession):
    svc = AudioPipelineService(db)
    return await svc.get_candidates(task_id)


@router.post("/tasks/{task_id}/audio/{candidate_id}/select", response_model=CandidateOut)
async def select_candidate(task_id: uuid.UUID, candidate_id: uuid.UUID, db: DBSession):
    svc = AudioPipelineService(db)
    candidate = await svc.select_candidate(task_id, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
