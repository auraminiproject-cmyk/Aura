import pytest


@pytest.mark.asyncio
async def test_guest_login_and_chat(client):
    login = await client.post("/api/v1/auth/guest", json={"display_name": "Test"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    chat = await client.post(
        "/api/v1/chat/message",
        json={"message": "wedding ki red lehenga kavali budget 5000", "language": "te"},
        headers=headers,
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body["session_id"]
    assert len(body["reply"]) > 10
    assert body["intent"] in ("design_request", "general", "greeting")
