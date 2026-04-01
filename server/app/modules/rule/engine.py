import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import AuditLog, CategoryRule

class RuleEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_rule_field(self, project_id: uuid.UUID, category: str, field_name: str, task_overrides: dict | None = None) -> tuple[Any, str]:
        if task_overrides and field_name in task_overrides:
            return task_overrides[field_name], "task_override"
        cat_rule = await self._find_active_rule(project_id, category, "category")
        if cat_rule and field_name in cat_rule.rule_body:
            return cat_rule.rule_body[field_name], "category"
        tpl_rule = await self._find_active_rule(project_id, category, "template")
        if tpl_rule and field_name in tpl_rule.rule_body:
            return tpl_rule.rule_body[field_name], "template"
        proj_rule = await self._find_active_rule(project_id, category, "project")
        if proj_rule and field_name in proj_rule.rule_body:
            return proj_rule.rule_body[field_name], "project"
        return None, "unresolved"

    async def resolve_all_fields(self, project_id: uuid.UUID, category: str, field_names: list[str], task_overrides: dict | None = None) -> dict[str, tuple[Any, str]]:
        results = {}
        for field_name in field_names:
            value, source = await self.resolve_rule_field(project_id, category, field_name, task_overrides)
            results[field_name] = (value, source)
        return results

    async def get_category_rule_body(self, project_id: uuid.UUID, category: str) -> dict | None:
        rule = await self._find_active_rule(project_id, category, "category")
        return rule.rule_body if rule else None

    async def _find_active_rule(self, project_id: uuid.UUID, category: str, level: str) -> CategoryRule | None:
        result = await self.db.execute(
            select(CategoryRule).where(
                CategoryRule.project_id == project_id,
                CategoryRule.category == category,
                CategoryRule.rule_level == level,
                CategoryRule.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def log_conflict(self, project_id: uuid.UUID, task_id: uuid.UUID | None, field_name: str, winning_source: str, losing_source: str) -> None:
        log = AuditLog(task_id=task_id, project_id=project_id, actor="system:rule_engine", action="rule_conflict", detail={"field": field_name, "winning_source": winning_source, "losing_source": losing_source})
        self.db.add(log)
        await self.db.flush()
