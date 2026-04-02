import pytest


@pytest.mark.asyncio
async def test_create_mapping(client, test_project):
    response = await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"action_map": [{"action_pattern": "*_Attack*"}]}}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["is_active"] == True


@pytest.mark.asyncio
async def test_get_mapping(client, test_project):
    await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"test": True}}
    )
    response = await client.get(f"/api/v1/projects/{test_project.project_id}/rules/mappings")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_mapping_versioning(client, test_project):
    await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"v1": True}}
    )
    resp2 = await client.put(
        f"/api/v1/projects/{test_project.project_id}/rules/mappings",
        json={"mapping_body": {"v2": True}}
    )
    assert resp2.json()["version"] == 2


@pytest.mark.asyncio
async def test_style_bible_get(client, test_project):
    resp = await client.get(f"/api/v1/projects/{test_project.project_id}/style-bible")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_style_bible_update(client, test_project):
    resp = await client.put(
        f"/api/v1/projects/{test_project.project_id}/style-bible",
        json={"style_bible": {"sonic_identity": {"summary": "dark action"}}}
    )
    assert resp.status_code == 200
    assert resp.json()["style_bible"]["sonic_identity"]["summary"] == "dark action"
