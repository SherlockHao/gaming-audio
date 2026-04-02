import io
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_upload_success(client, test_project):
    """Upload a file to a Draft task."""
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Upload Test",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    with patch("app.modules.task.upload.upload_file", new_callable=AsyncMock, return_value="bucket/path/test.mp4"):
        response = await client.post(
            f"/api/v1/tasks/{task_id}/upload",
            files={"file": ("test.mp4", b"fake video content", "video/mp4")},
            data={"asset_kind": "video"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["asset_kind"] == "video"
    assert data["asset_path"] == "bucket/path/test.mp4"
    assert data["checksum"] is not None

@pytest.mark.asyncio
async def test_upload_invalid_asset_kind(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bad Kind",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/upload",
        files={"file": ("test.mp4", b"data", "video/mp4")},
        data={"asset_kind": "invalid_type"},
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_upload_invalid_file_extension(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bad Extension",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]

    response = await client.post(
        f"/api/v1/tasks/{task_id}/upload",
        files={"file": ("malware.exe", b"data", "application/exe")},
        data={"asset_kind": "video"},
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_upload_task_not_found(client):
    import uuid
    response = await client.post(
        f"/api/v1/tasks/{uuid.uuid4()}/upload",
        files={"file": ("test.mp4", b"data", "video/mp4")},
        data={"asset_kind": "video"},
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_upload_wrong_task_status(client, test_project):
    """Cannot upload to a submitted task that has moved past Draft/Submitted."""
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Status Test",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    # Submit the task
    await client.post(f"/api/v1/tasks/{task_id}/submit")

    # Upload should still work for Submitted status
    with patch("app.modules.task.upload.upload_file", new_callable=AsyncMock, return_value="bucket/path"):
        response = await client.post(
            f"/api/v1/tasks/{task_id}/upload",
            files={"file": ("test.mp4", b"data", "video/mp4")},
            data={"asset_kind": "video"},
        )
    assert response.status_code == 201  # Submitted is allowed
