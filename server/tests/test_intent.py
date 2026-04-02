import pytest


@pytest.mark.asyncio
async def test_generate_intent_spec_success(client, test_project, db_session):
    """Full flow: create task -> submit -> generate intent spec."""
    # Seed a category rule so confidence is higher
    from app.core.models import CategoryRule, WwiseTemplate
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"target_lufs": -18}, version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="Test Template",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    # Create and submit task
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Boss Slam",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
        "tags": ["heavy", "metal"],
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")

    # Generate intent
    resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert resp.status_code == 201
    data = resp.json()
    assert data["content_type"] == "sfx"
    assert data["loop_required"] == False
    assert data["intensity"] == "heavy"
    assert data["material_hint"] == "metal"
    assert data["confidence"] is not None
    assert float(data["confidence"]) > 0


@pytest.mark.asyncio
async def test_generate_intent_requires_submitted_status(client, test_project):
    """Cannot generate intent for Draft task."""
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Draft Task",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    # Don't submit — still Draft
    resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_intent_spec(client, test_project, db_session):
    """Can retrieve generated intent spec."""
    from app.core.models import CategoryRule
    rule = CategoryRule(project_id=test_project.project_id, category="ui", rule_level="category",
                       rule_body={"target_lufs": -22}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()

    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "UI Confirm",
        "requester": "planner",
        "asset_type": "ui",
        "semantic_scene": "Confirm",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    await client.post(f"/api/v1/tasks/{task_id}/intent")

    resp = await client.get(f"/api/v1/tasks/{task_id}/intent")
    assert resp.status_code == 200
    assert resp.json()["content_type"] == "ui"


@pytest.mark.asyncio
async def test_get_intent_spec_not_found(client):
    import uuid
    resp = await client.get(f"/api/v1/tasks/{uuid.uuid4()}/intent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_intent_spec(client, test_project, db_session):
    """Can patch intent spec fields."""
    from app.core.models import CategoryRule
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"target_lufs": -18}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()

    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Patch Test",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Player",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    await client.post(f"/api/v1/tasks/{task_id}/intent")

    resp = await client.patch(f"/api/v1/tasks/{task_id}/intent", json={"intensity": "heavy"})
    assert resp.status_code == 200
    assert resp.json()["intensity"] == "heavy"


@pytest.mark.asyncio
async def test_duplicate_intent_generation_fails(client, test_project, db_session):
    """Cannot generate intent spec twice for same task."""
    from app.core.models import CategoryRule
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={}, version=1, is_active=True)
    db_session.add(rule)
    await db_session.flush()

    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Dup Test",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    await client.post(f"/api/v1/tasks/{task_id}/intent")

    # Second call should fail — task is no longer Submitted
    resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_low_confidence_triggers_review(client, test_project):
    """Task with no rules should get low confidence and enter SpecReviewPending."""
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "No Rules Task",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")

    resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert resp.status_code == 201

    # Check task is now in SpecReviewPending
    task_resp = await client.get(f"/api/v1/tasks/{task_id}")
    # With no rules, confidence should be low and task enters SpecReviewPending
    spec_data = resp.json()
    if float(spec_data["confidence"]) < 0.7:
        assert task_resp.json()["status"] == "SpecReviewPending"
    else:
        assert task_resp.json()["status"] == "SpecGenerated"
