import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.deps import DBSession
from app.modules.audio_pipeline.service import AudioPipelineService
from app.modules.audio_pipeline.qc_service import QCService

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


class QcReportOut(BaseModel):
    qc_report_id: uuid.UUID
    task_id: uuid.UUID
    candidate_id: uuid.UUID
    peak_result: dict | None
    loudness_result: dict | None
    spectrum_result: dict | None
    head_tail_result: dict | None
    format_result: dict | None
    qc_status: str
    created_at: datetime
    model_config = {"from_attributes": True}


@router.post("/tasks/{task_id}/audio/qc", response_model=list[QcReportOut], status_code=201)
async def run_qc(task_id: uuid.UUID, db: DBSession):
    svc = QCService(db)
    try:
        reports = await svc.run_qc(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return reports


@router.get("/tasks/{task_id}/audio/qc-reports", response_model=list[QcReportOut])
async def get_qc_reports(task_id: uuid.UUID, db: DBSession):
    svc = QCService(db)
    return await svc.get_qc_reports(task_id)
