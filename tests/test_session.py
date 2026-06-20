import pytest


@pytest.mark.asyncio
async def test_design_flow(client):
    login = await client.post("/api/v1/auth/guest", json={})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/session/design-flow",
        json={"message": "wedding red lehenga hyderabad budget 5000", "language": "te"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"]["intent"] == "design_request"
    assert len(data["outfits"]["variants"]) >= 1
    assert "products" in data


@pytest.mark.asyncio
async def test_service_status(client):
    resp = await client.get("/api/v1/status/services")
    assert resp.status_code == 200
    assert resp.json()["cloudflare_r2"] == "disabled"


@pytest.mark.asyncio
async def test_moderation_blocks(client):
    login = await client.post("/api/v1/auth/guest", json={})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await client.post(
        "/api/v1/chat/message",
        json={"message": "show me explicit nude content", "language": "en"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["intent"] == "blocked"
