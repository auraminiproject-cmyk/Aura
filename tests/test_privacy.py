import pytest


@pytest.mark.asyncio
async def test_privacy_export_and_consent(client):
    login = await client.post("/api/v1/auth/guest", json={})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    consent = await client.post("/api/v1/privacy/consent", headers=headers)
    assert consent.status_code == 200

    export = await client.get("/api/v1/privacy/export", headers=headers)
    assert export.status_code == 200
    assert "user" in export.json()


@pytest.mark.asyncio
async def test_refresh_token(client):
    login = await client.post("/api/v1/auth/guest", json={})
    refresh = login.json().get("refresh_token")
    assert refresh
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert resp.json()["access_token"]
