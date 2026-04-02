import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_wwise_import_mock(client, test_project, db_session):
    """Full flow through to Wwise import (mock mode)."""
    from app.core.models import CategoryRule, WwiseTemplate
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"format": {"sample_rate": 48000}, "duration": {"min_ms": 50, "max_ms": 5000},
                                  "loudness": {"target_lufs": -15, "tolerance_lu": 20, "true_peak_limit": -1.0},
                                  "head_tail": {"max_head_silence_ms": 100, "max_tail_silence_ms": 100}},
                       version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="T",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    # Create full pipeline: create -> upload -> submit -> intent -> generate -> qc -> wwise
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Wwise Test", "requester": "tester",
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

    # QC (candidates are placeholder WAVs, should pass with lenient rules)
    await client.post(f"/api/v1/tasks/{task_id}/audio/qc")

    task_check = await client.get(f"/api/v1/tasks/{task_id}")
    assert task_check.json()["status"] == "QCReady"

    # Wwise import
    resp = await client.post(f"/api/v1/tasks/{task_id}/wwise/import")
    assert resp.status_code == 201
    data = resp.json()
    assert data["import_status"] == "completed"
    assert len(data["object_entries"]) > 0
    assert "[MOCK]" in data["build_log"]

    task_check = await client.get(f"/api/v1/tasks/{task_id}")
    assert task_check.json()["status"] == "WwiseImported"


@pytest.mark.asyncio
async def test_build_bank_mock(client, test_project, db_session):
    """Build bank after Wwise import."""
    from app.core.models import CategoryRule, WwiseTemplate
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"format": {"sample_rate": 48000}, "duration": {"min_ms": 50, "max_ms": 5000},
                                  "loudness": {"target_lufs": -15, "tolerance_lu": 20, "true_peak_limit": -1.0},
                                  "head_tail": {"max_head_silence_ms": 100, "max_tail_silence_ms": 100}},
                       version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="T",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bank Test", "requester": "tester",
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
    await client.post(f"/api/v1/tasks/{task_id}/audio/qc")
    await client.post(f"/api/v1/tasks/{task_id}/wwise/import")

    # Build bank
    resp = await client.post(f"/api/v1/tasks/{task_id}/wwise/build-bank")
    assert resp.status_code == 200
    assert resp.json()["import_status"] == "bank_built"

    task_check = await client.get(f"/api/v1/tasks/{task_id}")
    assert task_check.json()["status"] == "BankBuilt"


@pytest.mark.asyncio
async def test_wwise_import_requires_qc_ready(client, test_project):
    """Cannot import to Wwise without QC passing first."""
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bad Wwise", "requester": "tester",
        "asset_type": "sfx", "semantic_scene": "Boss", "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]
    resp = await client.post(f"/api/v1/tasks/{task_id}/wwise/import")
    assert resp.status_code == 400
