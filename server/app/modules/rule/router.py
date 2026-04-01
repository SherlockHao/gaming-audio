import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.core.deps import DBSession
from app.modules.rule.service import RuleService

router = APIRouter(tags=["rules"])

class CategoryRuleCreate(BaseModel):
    project_id: uuid.UUID
    category: str
    rule_level: str = "category"
    rule_body: dict

class CategoryRuleOut(BaseModel):
    rule_id: uuid.UUID
    project_id: uuid.UUID
    category: str
    rule_level: str
    rule_body: dict
    version: int
    is_active: bool
    model_config = {"from_attributes": True}

class WwiseTemplateCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    template_type: str
    template_body: dict

class WwiseTemplateOut(BaseModel):
    template_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    template_type: str
    template_body: dict
    version: int
    is_active: bool
    model_config = {"from_attributes": True}

@router.post("/rules/categories", response_model=CategoryRuleOut, status_code=201)
async def create_category_rule(data: CategoryRuleCreate, db: DBSession):
    svc = RuleService(db)
    return await svc.create_category_rule(project_id=data.project_id, category=data.category, rule_level=data.rule_level, rule_body=data.rule_body)

@router.get("/rules/categories", response_model=list[CategoryRuleOut])
async def list_category_rules(db: DBSession, project_id: uuid.UUID = Query(...), category: str | None = None):
    svc = RuleService(db)
    return await svc.list_category_rules(project_id, category)

@router.put("/rules/categories/{rule_id}", response_model=CategoryRuleOut)
async def update_category_rule(rule_id: uuid.UUID, data: dict, db: DBSession):
    svc = RuleService(db)
    rule = await svc.update_category_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.post("/rules/wwise-templates", response_model=WwiseTemplateOut, status_code=201)
async def create_wwise_template(data: WwiseTemplateCreate, db: DBSession):
    svc = RuleService(db)
    return await svc.create_wwise_template(project_id=data.project_id, name=data.name, template_type=data.template_type, template_body=data.template_body)

@router.get("/rules/wwise-templates", response_model=list[WwiseTemplateOut])
async def list_wwise_templates(db: DBSession, project_id: uuid.UUID = Query(...)):
    svc = RuleService(db)
    return await svc.list_wwise_templates(project_id)
