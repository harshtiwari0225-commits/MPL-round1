import pytest


@pytest.mark.asyncio
async def test_admin_routes_unauthorized(client):
    # Without admin-passcode header, returns 422 (Unprocessable Entity)
    response = await client.get("/api/admin/teams")
    assert response.status_code == 422

    # With invalid admin-passcode header, returns 401
    response = await client.get("/api/admin/teams", headers={"admin-passcode": "wrong_passcode"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_create_and_list_teams(client):
    headers = {"admin-passcode": "admin123"}

    # Create team
    create_resp = await client.post(
        "/api/admin/teams",
        headers=headers,
        json={"name": "Admin Created Team", "passcode": "pass123"},
    )
    assert create_resp.status_code == 200
    team_data = create_resp.json()
    assert team_data["message"] == "Team created successfully"
    assert "id" in team_data

    # List teams
    list_resp = await client.get("/api/admin/teams", headers=headers)
    assert list_resp.status_code == 200
    teams = list_resp.json()
    assert any(t["name"] == "Admin Created Team" for t in teams)


@pytest.mark.asyncio
async def test_admin_leaderboard(client):
    response = await client.get("/api/admin/leaderboard")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_judge_health(client):
    headers = {"admin-passcode": "admin123"}
    response = await client.get("/api/admin/judge/health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "mock"
    assert data["healthy"] is True
