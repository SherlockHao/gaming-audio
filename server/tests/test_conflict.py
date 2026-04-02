import pytest
from app.core.models import AuditLog, CategoryRule
from app.modules.rule.engine import RuleEngine
from sqlalchemy import select


@pytest.mark.asyncio
async def test_resolve_with_conflict_logs_when_values_differ(db_session, test_project):
    """When category and template rules have different values, conflict should be logged."""
    cat_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                           rule_body={"target_lufs": -18}, version=1, is_active=True)
    tpl_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="template",
                           rule_body={"target_lufs": -16}, version=1, is_active=True)
    db_session.add_all([cat_rule, tpl_rule])
    await db_session.flush()

    engine = RuleEngine(db_session)
    value, source = await engine.resolve_with_conflict_check(
        test_project.project_id, "sfx", "target_lufs", task_id=None
    )
    assert value == -18  # category wins over template
    assert source == "category"

    # Check that a conflict was logged
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "rule_conflict")
    )
    conflicts = list(result.scalars().all())
    assert len(conflicts) >= 1
    assert conflicts[0].detail["field"] == "target_lufs"
    assert conflicts[0].detail["winning_source"] == "category"
    assert conflicts[0].detail["losing_source"] == "template"


@pytest.mark.asyncio
async def test_resolve_with_conflict_no_log_when_values_match(db_session, test_project):
    """When category and template rules have same values, no conflict should be logged."""
    cat_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                           rule_body={"target_lufs": -18}, version=1, is_active=True)
    tpl_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="template",
                           rule_body={"target_lufs": -18}, version=1, is_active=True)
    db_session.add_all([cat_rule, tpl_rule])
    await db_session.flush()

    engine = RuleEngine(db_session)
    value, source = await engine.resolve_with_conflict_check(
        test_project.project_id, "sfx", "target_lufs"
    )
    assert value == -18

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "rule_conflict")
    )
    conflicts = list(result.scalars().all())
    assert len(conflicts) == 0


@pytest.mark.asyncio
async def test_resolve_with_conflict_task_override_wins(db_session, test_project):
    """Task override should win and conflict logged against category."""
    cat_rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                           rule_body={"target_lufs": -18}, version=1, is_active=True)
    db_session.add(cat_rule)
    await db_session.flush()

    engine = RuleEngine(db_session)
    value, source = await engine.resolve_with_conflict_check(
        test_project.project_id, "sfx", "target_lufs",
        task_overrides={"target_lufs": -14},
    )
    assert value == -14
    assert source == "task_override"

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "rule_conflict")
    )
    conflicts = list(result.scalars().all())
    assert len(conflicts) >= 1
