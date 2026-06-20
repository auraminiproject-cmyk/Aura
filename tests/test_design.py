import pytest


@pytest.mark.asyncio
async def test_generate_outfits(client):
    login = await client.post("/api/v1/auth/guest", json={})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/design/outfits",
        json={"brief": "red lehenga wedding hyderabad 5000"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["variants"]) >= 1
