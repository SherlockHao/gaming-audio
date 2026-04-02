import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.deps import DBSession
from app.modules.intent.service import IntentService

router = APIRouter(tags=["intent"])


class IntentSpecOut(BaseModel):
    intent_id: uuid.UUID
    task_id: uuid.UUID
    content_type: str
    semantic_role: str | None
    intensity: str | None
    material_hint: str | None
    timing_points: list | None
    loop_required: bool
    variation_count: int
    design_pattern: str | None
    category_rule_id: uuid.UUID | None
    wwise_template_id: uuid.UUID | None
    ue_binding_strategy: str | None
    confidence: float | None
    unresolved_fields: list | None
    model_config = {"from_attributes": True}


class IntentSpecUpdate(BaseModel):
    intensity: str | None = None
    material_hint: str | None = None
    design_pattern: str | None = None
    ue_binding_strategy: str | None = None


@router.post("/tasks/{task_id}/intent", response_model=IntentSpecOut, status_code=201)
async def generate_intent_spec(task_id: uuid.UUID, db: DBSession):
    svc = IntentService(db)
    try:
        spec = await svc.generate_intent_spec(task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return spec


@router.get("/tasks/{task_id}/intent", response_model=IntentSpecOut)
async def get_intent_spec(task_id: uuid.UUID, db: DBSession):
    svc = IntentService(db)
    spec = await svc.get_intent_spec(task_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Intent spec not found")
    return spec


@router.patch("/tasks/{task_id}/intent", response_model=IntentSpecOut)
async def update_intent_spec(task_id: uuid.UUID, data: IntentSpecUpdate, db: DBSession):
    svc = IntentService(db)
    try:
        spec = await svc.update_intent_spec(task_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not spec:
        raise HTTPException(status_code=404, detail="Intent spec not found")
    return spec
