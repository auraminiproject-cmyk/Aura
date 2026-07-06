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
    assert data["intent"] == "design_request"
    assert data.get("outfits") is None or len(data["outfits"]) >= 1
    # Note: run_graph may return None for outfits if the planner goal is not PROPOSE_OUTFIT or FINALIZE.
    # In this test case, the planner goal is PROPOSE_OUTFIT or FINALIZE.
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
