import pytest


@pytest.mark.asyncio
async def test_style_feedback(client):
    login = await client.post("/api/v1/auth/guest", json={})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/feedback/style",
        json={"liked": True, "tags": ["wedding", "red"]},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["liked_tags"]
