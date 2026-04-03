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
        upload_resp = await client.post(f"/api/v1/tasks/{task_id}/upload",
                         files={"file": ("t.mp4", b"f", "video/mp4")}, data={"asset_kind": "video"})
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    submit_resp = await client.post(f"/api/v1/tasks/{task_id}/submit")
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    intent_resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert intent_resp.status_code in (200, 201), f"Intent failed: {intent_resp.text}"

    with patch("app.modules.audio_pipeline.service.upload_file", new_callable=AsyncMock, return_value="b/c.wav"):
        gen_resp = await client.post(f"/api/v1/tasks/{task_id}/audio/generate")
    assert gen_resp.status_code == 201, f"Generate failed: {gen_resp.text}"

    # QC: mock analysis so placeholder candidates return valid audio measurements
    mock_analysis = {
        "sample_rate": 48000, "bit_depth": 24, "channels": 1,
        "duration_ms": 1000, "peak_dbfs": -6.0, "rms_dbfs": -18.0,
        "head_silence_ms": 0, "tail_silence_ms": 0,
    }
    with patch("app.modules.audio_pipeline.qc_service.QCService._analyze_candidate",
               new_callable=AsyncMock, return_value=mock_analysis):
        qc_resp = await client.post(f"/api/v1/tasks/{task_id}/audio/qc")
    assert qc_resp.status_code == 201, f"QC failed: {qc_resp.text}"

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
        upload_resp = await client.post(f"/api/v1/tasks/{task_id}/upload",
                         files={"file": ("t.mp4", b"f", "video/mp4")}, data={"asset_kind": "video"})
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    submit_resp = await client.post(f"/api/v1/tasks/{task_id}/submit")
    assert submit_resp.status_code == 200, f"Submit failed: {submit_resp.text}"
    intent_resp = await client.post(f"/api/v1/tasks/{task_id}/intent")
    assert intent_resp.status_code in (200, 201), f"Intent failed: {intent_resp.text}"
    with patch("app.modules.audio_pipeline.service.upload_file", new_callable=AsyncMock, return_value="b/c.wav"):
        gen_resp = await client.post(f"/api/v1/tasks/{task_id}/audio/generate")
    assert gen_resp.status_code == 201, f"Generate failed: {gen_resp.text}"
    mock_analysis = {
        "sample_rate": 48000, "bit_depth": 24, "channels": 1,
        "duration_ms": 1000, "peak_dbfs": -6.0, "rms_dbfs": -18.0,
        "head_silence_ms": 0, "tail_silence_ms": 0,
    }
    with patch("app.modules.audio_pipeline.qc_service.QCService._analyze_candidate",
               new_callable=AsyncMock, return_value=mock_analysis):
        qc_resp = await client.post(f"/api/v1/tasks/{task_id}/audio/qc")
    assert qc_resp.status_code == 201, f"QC failed: {qc_resp.text}"
    import_resp = await client.post(f"/api/v1/tasks/{task_id}/wwise/import")
    assert import_resp.status_code == 201, f"Wwise import failed: {import_resp.text}"

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
