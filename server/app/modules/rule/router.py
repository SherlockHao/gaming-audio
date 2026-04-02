import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.core.deps import DBSession
from app.modules.rule.service import RuleService

router = APIRouter(tags=["rules"])

class CategoryRuleCreate(BaseModel):
    category: str
    rule_level: str = "category"
    rule_body: dict

class CategoryRuleUpdate(BaseModel):
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

class StyleBibleUpdate(BaseModel):
    style_bible: dict

class StyleBibleOut(BaseModel):
    project_id: uuid.UUID
    name: str
    style_bible: dict | None
    model_config = {"from_attributes": True}

@router.post("/projects/{project_id}/rules/categories", response_model=CategoryRuleOut, status_code=201)
async def create_category_rule(project_id: uuid.UUID, data: CategoryRuleCreate, db: DBSession):
    svc = RuleService(db)
    return await svc.create_category_rule(project_id=project_id, category=data.category, rule_level=data.rule_level, rule_body=data.rule_body)

@router.get("/projects/{project_id}/rules/categories", response_model=list[CategoryRuleOut])
async def list_category_rules(project_id: uuid.UUID, db: DBSession, category: str | None = None):
    svc = RuleService(db)
    return await svc.list_category_rules(project_id, category)

@router.put("/projects/{project_id}/rules/categories/{rule_id}", response_model=CategoryRuleOut)
async def update_category_rule(project_id: uuid.UUID, rule_id: uuid.UUID, data: CategoryRuleUpdate, db: DBSession):
    svc = RuleService(db)
    rule = await svc.update_category_rule(rule_id, data.rule_body)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.post("/projects/{project_id}/rules/wwise-templates", response_model=WwiseTemplateOut, status_code=201)
async def create_wwise_template(project_id: uuid.UUID, data: WwiseTemplateCreate, db: DBSession):
    svc = RuleService(db)
    return await svc.create_wwise_template(project_id=project_id, name=data.name, template_type=data.template_type, template_body=data.template_body)

@router.get("/projects/{project_id}/rules/wwise-templates", response_model=list[WwiseTemplateOut])
async def list_wwise_templates(project_id: uuid.UUID, db: DBSession):
    svc = RuleService(db)
    return await svc.list_wwise_templates(project_id)

# --- Style Bible ---

class MappingDictOut(BaseModel):
    mapping_id: uuid.UUID
    project_id: uuid.UUID
    mapping_body: dict
    version: int
    is_active: bool
    model_config = {"from_attributes": True}

class MappingDictUpdate(BaseModel):
    mapping_body: dict

@router.get("/projects/{project_id}/rules/mappings", response_model=MappingDictOut | None)
async def get_mapping(project_id: uuid.UUID, db: DBSession):
    svc = RuleService(db)
    return await svc.get_active_mapping(project_id)

@router.put("/projects/{project_id}/rules/mappings", response_model=MappingDictOut)
async def update_mapping(project_id: uuid.UUID, data: MappingDictUpdate, db: DBSession):
    svc = RuleService(db)
    return await svc.update_mapping(project_id, data.mapping_body)

@router.get("/projects/{project_id}/style-bible", response_model=StyleBibleOut)
async def get_style_bible(project_id: uuid.UUID, db: DBSession):
    svc = RuleService(db)
    project = await svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}/style-bible", response_model=StyleBibleOut)
async def update_style_bible(project_id: uuid.UUID, data: StyleBibleUpdate, db: DBSession):
    svc = RuleService(db)
    project = await svc.update_style_bible(project_id, data.style_bible)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
