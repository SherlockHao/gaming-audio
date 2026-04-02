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

@pytest.mark.asyncio
async def test_resolve_from_template_rule(db_session, test_project):
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="template", rule_body={"conversion_quality": 4}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "conversion_quality")
    assert value == 4
    assert source == "template"

@pytest.mark.asyncio
async def test_resolve_from_project_rule(db_session, test_project):
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="project", rule_body={"max_voices": 32}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "max_voices")
    assert value == 32
    assert source == "project"

@pytest.mark.asyncio
async def test_category_overrides_template(db_session, test_project):
    """When both category and template rules exist, category should win."""
    tpl_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="template", rule_body={"target_lufs": -16}, version=1, is_active=True)
    cat_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category", rule_body={"target_lufs": -18}, version=1, is_active=True)
    db_session.add_all([tpl_rule, cat_rule])
    await db_session.flush()
    engine = RuleEngine(db_session)
    value, source = await engine.resolve_rule_field(test_project.project_id, "sfx", "target_lufs")
    assert value == -18
    assert source == "category"

@pytest.mark.asyncio
async def test_resolve_all_fields(db_session, test_project):
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category", rule_body={"target_lufs": -18, "sample_rate": 48000}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()
    engine = RuleEngine(db_session)
    results = await engine.resolve_all_fields(test_project.project_id, "sfx", ["target_lufs", "sample_rate", "missing"])
    assert results["target_lufs"] == (-18, "category")
    assert results["sample_rate"] == (48000, "category")
    assert results["missing"] == (None, "unresolved")
