import uuid
import pytest

@pytest.mark.asyncio
async def test_create_task(client, test_project):
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Boss Slam Attack",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
        "tags": ["heavy", "melee"],
        "priority": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Boss Slam Attack"
    assert data["status"] == "Draft"
    assert data["asset_type"] == "sfx"

@pytest.mark.asyncio
async def test_create_task_invalid_asset_type(client, test_project):
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "VO Task",
        "requester": "planner_zhang",
        "asset_type": "vo",
        "semantic_scene": "NPC",
        "play_mode": "one_shot",
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_list_tasks(client, test_project):
    for title in ["Task A", "Task B"]:
        await client.post("/api/v1/tasks", json={
            "project_id": str(test_project.project_id),
            "title": title,
            "requester": "planner_zhang",
            "asset_type": "sfx",
            "semantic_scene": "Boss",
            "play_mode": "one_shot",
        })
    response = await client.get("/api/v1/tasks", params={"project_id": str(test_project.project_id)})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2

@pytest.mark.asyncio
async def test_get_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Get Test",
        "requester": "planner_zhang",
        "asset_type": "ui",
        "semantic_scene": "SystemUI",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    response = await client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"

@pytest.mark.asyncio
async def test_update_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Update Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    response = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "Updated Title", "priority": 5})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["priority"] == 5

@pytest.mark.asyncio
async def test_submit_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Submit Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    response = await client.post(f"/api/v1/tasks/{task_id}/submit")
    assert response.status_code == 200
    assert response.json()["status"] == "Submitted"

@pytest.mark.asyncio
async def test_cannot_edit_submitted_task(client, test_project):
    create_resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Lock Test",
        "requester": "planner_zhang",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = create_resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    response = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New Title"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_create_task_invalid_play_mode(client, test_project):
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Bad Mode",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "continuous",  # invalid
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_nonexistent_task(client):
    response = await client.get(f"/api/v1/tasks/{uuid.uuid4()}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_nonexistent_task(client):
    response = await client.patch(f"/api/v1/tasks/{uuid.uuid4()}", json={"title": "X"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_submit_nonexistent_task(client):
    response = await client.post(f"/api/v1/tasks/{uuid.uuid4()}/submit")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_double_submit(client, test_project):
    resp = await client.post("/api/v1/tasks", json={
        "project_id": str(test_project.project_id),
        "title": "Double Submit",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    task_id = resp.json()["task_id"]
    await client.post(f"/api/v1/tasks/{task_id}/submit")
    resp2 = await client.post(f"/api/v1/tasks/{task_id}/submit")
    assert resp2.status_code == 400

@pytest.mark.asyncio
async def test_create_task_invalid_project_id(client):
    """Creating a task with non-existent project_id should return 400, not 500."""
    response = await client.post("/api/v1/tasks", json={
        "project_id": str(uuid.uuid4()),
        "title": "Bad Project",
        "requester": "planner",
        "asset_type": "sfx",
        "semantic_scene": "Boss",
        "play_mode": "one_shot",
    })
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_create_project(client):
    response = await client.post("/api/v1/projects", json={"name": "Test Project"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Project"

@pytest.mark.asyncio
async def test_list_projects(client):
    await client.post("/api/v1/projects", json={"name": "P1"})
    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    assert len(response.json()) >= 1
