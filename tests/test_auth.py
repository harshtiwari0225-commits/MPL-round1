import pytest

from app.models import Team


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/api/auth/login",
        json={"name": "NonExistentTeam", "passcode": "wrong"},
    )
    assert response.status_code == 401
    assert "Invalid team name or passcode" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    # Create a team in the DB
    team = Team(name="Test Team Auth", passcode="secret123")
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    response = await client.post(
        "/api/auth/login",
        json={"name": "Test Team Auth", "passcode": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Team Auth"
    assert data["session_token"] is not None
