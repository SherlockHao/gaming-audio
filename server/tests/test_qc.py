import pytest
from app.modules.audio_pipeline.processor import analyze_audio_file, run_qc_checks
from app.modules.audio_pipeline.generator import _generate_placeholder_wav
import os


def test_analyze_placeholder_wav():
    """Analyze a generated placeholder WAV."""
    path = _generate_placeholder_wav(duration_ms=500, sample_rate=48000)
    try:
        result = analyze_audio_file(path)
        assert result["sample_rate"] == 48000
        assert result["channels"] == 1
        assert result["duration_ms"] > 0
        assert result["peak_dbfs"] < 0
    finally:
        os.unlink(path)


def test_qc_pass_with_matching_rule():
    """QC should pass when analysis matches category rule."""
    analysis = {
        "sample_rate": 48000, "bit_depth": 16, "channels": 1,
        "duration_ms": 1000, "peak_dbfs": -20.0, "rms_dbfs": -30.0,
        "head_silence_ms": 0, "tail_silence_ms": 0,
    }
    rule = {
        "format": {"sample_rate": 48000, "bit_depth": 24, "channels": "mono"},
        "loudness": {"target_lufs": -15, "tolerance_lu": 20, "true_peak_limit": -1.0},
        "duration": {"min_ms": 50, "max_ms": 5000},
        "head_tail": {"max_head_silence_ms": 10, "max_tail_silence_ms": 50},
    }
    results = run_qc_checks(analysis, rule)
    assert results["qc_status"] == "passed"


def test_qc_fail_wrong_sample_rate():
    """QC should fail when sample rate doesn't match."""
    analysis = {
        "sample_rate": 44100, "bit_depth": 16, "channels": 1,
        "duration_ms": 1000, "peak_dbfs": -20.0, "rms_dbfs": -30.0,
        "head_silence_ms": 0, "tail_silence_ms": 0,
    }
    rule = {"format": {"sample_rate": 48000}, "loudness": {"true_peak_limit": -1.0},
            "duration": {"min_ms": 50, "max_ms": 5000}, "head_tail": {}}
    results = run_qc_checks(analysis, rule)
    assert results["qc_status"] == "failed"


def test_qc_fail_duration_out_of_range():
    """QC should fail when duration is too short."""
    analysis = {
        "sample_rate": 48000, "bit_depth": 16, "channels": 1,
        "duration_ms": 10, "peak_dbfs": -20.0, "rms_dbfs": -30.0,
        "head_silence_ms": 0, "tail_silence_ms": 0,
    }
    rule = {"format": {"sample_rate": 48000}, "loudness": {"true_peak_limit": -1.0},
            "duration": {"min_ms": 50, "max_ms": 5000}, "head_tail": {}}
    results = run_qc_checks(analysis, rule)
    assert results["qc_status"] == "failed"


def test_qc_no_rule_passes():
    """QC passes when no category rule exists."""
    analysis = {"sample_rate": 48000}
    results = run_qc_checks(analysis, None)
    assert results["qc_status"] == "passed"


@pytest.mark.asyncio
async def test_qc_api_all_fail(client, test_project, db_session):
    """When all candidates fail QC, task should enter QCFailed."""
    from app.core.models import CategoryRule, WwiseTemplate
    from unittest.mock import AsyncMock, patch

    # Rule with strict sample_rate that won't match placeholder WAV
    rule = CategoryRule(project_id=test_project.project_id, category="sfx", rule_level="category",
                       rule_body={"format": {"sample_rate": 96000},  # Placeholder is 48000 -> will fail
                                  "duration": {"min_ms": 50, "max_ms": 5000},
                                  "loudness": {"true_peak_limit": -1.0},
                                  "head_tail": {}},
                       version=1, is_active=True)
    template = WwiseTemplate(project_id=test_project.project_id, name="T",
                            template_type="action_game", template_body={}, version=1, is_active=True)
    db_session.add_all([rule, template])
    await db_session.flush()

    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "QC Fail Test", "requester": "tester",
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

    # Run QC - should fail because sample_rate 48000 != 96000
    resp = await client.post(f"/api/v1/tasks/{task_id}/audio/qc")
    assert resp.status_code == 201
    reports = resp.json()
    assert all(r["qc_status"] == "failed" for r in reports)

    # Task should be QCFailed
    task_resp = await client.get(f"/api/v1/tasks/{task_id}")
    assert task_resp.json()["status"] == "QCFailed"
