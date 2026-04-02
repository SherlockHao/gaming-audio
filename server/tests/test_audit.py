import pytest

@pytest.mark.asyncio
async def test_audit_log_created_on_task_create(client, test_project):
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Audit Test",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]

    log_resp = await client.get(f"/api/v1/tasks/{task_id}/audit-log")
    assert log_resp.status_code == 200
    logs = log_resp.json()
    assert len(logs) >= 1
    assert any(log["action"] == "task_created" for log in logs)

@pytest.mark.asyncio
async def test_audit_log_created_on_submit(client, test_project):
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Submit Audit",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")

    log_resp = await client.get(f"/api/v1/tasks/{task_id}/audit-log")
    logs = log_resp.json()
    actions = [log["action"] for log in logs]
    assert "task_created" in actions
    assert "task_submit" in actions
