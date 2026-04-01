import pytest
from app.core.models import CategoryRule
from app.modules.rule.engine import RuleEngine

@pytest.mark.asyncio
async def test_resolve_from_category_rule(db_session, test_project):
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category", rule_body={"target_lufs": -18, "true_peak_limit": -1.0}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "target_lufs")
    assert value == -18
    assert source == "category"

@pytest.mark.asyncio
async def test_task_override_takes_priority(db_session, test_project):
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category", rule_body={"target_lufs": -18}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "target_lufs", task_overrides={"target_lufs": -14})
    assert value == -14
    assert source == "task_override"

@pytest.mark.asyncio
async def test_unresolved_field(db_session, test_project):
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "nonexistent_field")
    assert value is None
    assert source == "unresolved"
