import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import CategoryRule, MappingDictionary, Project, WwiseTemplate

class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category_rule(self, project_id: uuid.UUID, category: str, rule_level: str, rule_body: dict) -> CategoryRule:
        rule = CategoryRule(project_id=project_id, category=category, rule_level=rule_level, rule_body=rule_body, version=1, is_active=True)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def get_category_rule(self, rule_id: uuid.UUID) -> CategoryRule | None:
        result = await self.db.execute(select(CategoryRule).where(CategoryRule.rule_id == rule_id))
        return result.scalar_one_or_none()

    async def list_category_rules(self, project_id: uuid.UUID, category: str | None = None) -> list[CategoryRule]:
        query = select(CategoryRule).where(CategoryRule.project_id == project_id, CategoryRule.is_active == True)
        if category:
            query = query.where(CategoryRule.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_category_rule(self, rule_id: uuid.UUID, rule_body: dict) -> CategoryRule | None:
        old_rule = await self.get_category_rule(rule_id)
        if not old_rule:
            return None
        old_rule.is_active = False
        new_rule = CategoryRule(project_id=old_rule.project_id, category=old_rule.category, rule_level=old_rule.rule_level, rule_body=rule_body, version=old_rule.version + 1, is_active=True)
        self.db.add(new_rule)
        await self.db.commit()
        await self.db.refresh(new_rule)
        return new_rule

    async def create_wwise_template(self, project_id: uuid.UUID, name: str, template_type: str, template_body: dict) -> WwiseTemplate:
        template = WwiseTemplate(project_id=project_id, name=name, template_type=template_type, template_body=template_body, version=1, is_active=True)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def list_wwise_templates(self, project_id: uuid.UUID) -> list[WwiseTemplate]:
        result = await self.db.execute(select(WwiseTemplate).where(WwiseTemplate.project_id == project_id, WwiseTemplate.is_active == True))
        return list(result.scalars().all())

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.project_id == project_id))
        return result.scalar_one_or_none()

    async def get_active_mapping(self, project_id: uuid.UUID) -> MappingDictionary | None:
        result = await self.db.execute(
            select(MappingDictionary).where(
                MappingDictionary.project_id == project_id,
                MappingDictionary.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def update_mapping(self, project_id: uuid.UUID, mapping_body: dict) -> MappingDictionary:
        old = await self.get_active_mapping(project_id)
        if old:
            old.is_active = False
            new_version = old.version + 1
        else:
            new_version = 1
        mapping = MappingDictionary(
            project_id=project_id, mapping_body=mapping_body,
            version=new_version, is_active=True,
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def update_style_bible(self, project_id: uuid.UUID, style_bible: dict) -> Project | None:
        project = await self.get_project(project_id)
        if not project:
            return None
        project.style_bible = style_bible
        await self.db.commit()
        await self.db.refresh(project)
        return project
