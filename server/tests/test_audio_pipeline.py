import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_generate_audio_candidates(client, test_project, db_session):
    """Full flow: create -> submit -> intent -> generate audio."""
    from app.core.models import CategoryRule, WwiseTemplate
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"format": {"sample_rate": 48000}, "duration": {"min_ms": 50, "max_ms": 5000},
                                  "loudness": {"target_lufs": -15, "tolerance_lu": 3, "true_peak_limit": -1.0}},
                       version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="Test",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    # Create and submit task
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Audio Gen Test", "requester": "tester",
        "asset_type": "sfx", "semantic_scene": "Boss", "play_mode": "one_shot",
        "tags": ["heavy", "metal"],
    })
    task_id = resp.json()["task_id"]

    # Need to upload a file first (submit requires it)
    with patch("app.modules.task.upload.upload_file", new_callable=AsyncMock, return_value="bucket/test.mp4"):
        await client.post(f"/api/v1/tasks/{task_id}/upload",
                         files={"file": ("test.mp4", b"fake", "video/mp4")}, data={"asset_kind": "video"})
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    await client.post(f"/api/v1/tasks/{task_id}/intent")

    # Generate audio (mock upload_file to avoid MinIO dependency)
    with patch("app.modules.audio_pipeline.service.upload_file", new_callable=AsyncMock, return_value="bucket/candidate.wav"):
        resp = await client.post(f"/api/v1/tasks/{task_id}/audio/generate")

    assert resp.status_code == 201
    candidates = resp.json()
    assert len(candidates) >= 3
    assert candidates[0]["stage"] == "source"
    assert candidates[0]["selected"] is True

    # Check task state
    task_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert task_resp.json()["status"] == "AudioGenerated"


@pytest.mark.asyncio
async def test_list_candidates(client, test_project, db_session):
    """Can list candidates after generation."""
    from app.core.models import CategoryRule, WwiseTemplate
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"duration": {"min_ms": 50, "max_ms": 5000}}, version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="T",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "List Cand Test", "requester": "tester",
        "asset_type": "sfx", "semantic_scene": "Boss", "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]
    with patch("app.modules.task.upload.upload_file", new_callable=AsyncMock, return_value="b/t.mp4"):
        await client.post(f"/api/v1/tasks/{task_id}/upload",
                         files={"file": ("t.mp4", b"f", "video/mp4")}, data={"asset_kind": "video"})
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    await client.post(f"/api/v1/tasks/{task_id}/intent")
    with patch("app.modules.audio_pipeline.service.upload_file", new_callable=AsyncMock, return_value="b/c.wav"):
        await client.post(f"/api/v1/tasks/{task_id}/audio/generate")

    resp = await client.get(f"/api/v1/tasks/{task_id}/audio/candidates")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


@pytest.mark.asyncio
async def test_generate_requires_spec_generated(client, test_project):
    """Cannot generate audio for Draft task."""
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bad State", "requester": "tester",
        "asset_type": "sfx", "semantic_scene": "Boss", "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]
    resp = await client.post(f"/api/v1/tasks/{task_id}/audio/generate")
    assert resp.status_code == 400
