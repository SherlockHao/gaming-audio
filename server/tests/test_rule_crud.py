import pytest

@pytest.mark.asyncio
async def test_create_category_rule(client, test_project):
    pid = str(test_project.project_id)
    response = await client.post(f"/api/v1/projects/{pid}/rules/categories", json={
        "category": "sfx",
        "rule_level": "category",
        "rule_body": {"target_lufs": -18, "sample_rate": 48000},
    })
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "sfx"
    assert data["version"] == 1
    assert data["is_active"] == True

@pytest.mark.asyncio
async def test_list_category_rules(client, test_project):
    pid = str(test_project.project_id)
    await client.post(f"/api/v1/projects/{pid}/rules/categories", json={
        "category": "sfx",
        "rule_level": "category",
        "rule_body": {"target_lufs": -18},
    })
    response = await client.get(f"/api/v1/projects/{pid}/rules/categories")
    assert response.status_code == 200
    assert len(response.json()) >= 1

@pytest.mark.asyncio
async def test_update_category_rule_versioning(client, test_project):
    pid = str(test_project.project_id)
    create_resp = await client.post(f"/api/v1/projects/{pid}/rules/categories", json={
        "category": "ui",
        "rule_level": "category",
        "rule_body": {"target_lufs": -22},
    })
    assert create_resp.status_code == 201
    rule_id = create_resp.json()["rule_id"]

    update_resp = await client.put(
        f"/api/v1/projects/{pid}/rules/categories/{rule_id}",
        json={"rule_body": {"target_lufs": -20}},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["version"] == 2
    assert data["rule_body"]["target_lufs"] == -20
    assert data["is_active"] == True

@pytest.mark.asyncio
async def test_create_wwise_template(client, test_project):
    pid = str(test_project.project_id)
    response = await client.post(f"/api/v1/projects/{pid}/rules/wwise-templates", json={
        "name": "Action Game SFX",
        "template_type": "action_game",
        "template_body": {"hierarchy": {"root": "ActionGame"}},
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Action Game SFX"

@pytest.mark.asyncio
async def test_list_wwise_templates(client, test_project):
    pid = str(test_project.project_id)
    await client.post(f"/api/v1/projects/{pid}/rules/wwise-templates", json={
        "name": "Template1",
        "template_type": "action_game",
        "template_body": {},
    })
    response = await client.get(f"/api/v1/projects/{pid}/rules/wwise-templates")
    assert response.status_code == 200
    assert len(response.json()) >= 1
