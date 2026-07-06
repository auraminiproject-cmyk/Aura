import asyncio
import httpx
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://127.0.0.1:8000"

async def test_flow():
    async with httpx.AsyncClient(timeout=120) as client:
        print("1. Auth: Guest Login")
        auth_resp = await client.post(f"{API_URL}/api/v1/auth/guest", json={"display_name": "TestUser"})
        if auth_resp.status_code != 200:
            print("Auth failed:", auth_resp.text)
            return
        
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Auth success, token acquired.")
        
        print("2. Avatar POST")
        with open("test_body.jpg", "rb") as f:
            files = {"front": ("test_body.jpg", f, "image/jpeg")}
            avatar_resp = await client.post(f"{API_URL}/api/v1/avatar/analyze", headers=headers, files=files, data={"height_cm": "170"})
            
        if avatar_resp.status_code != 200:
            print("Avatar analysis failed:", avatar_resp.text)
            return
        print("Avatar analysis success:", avatar_resp.json()["build_type"])
        
        print("3. Voice Chat POST (Text-based for testing)")
        chat_resp = await client.post(f"{API_URL}/api/v1/voice/converse-text", headers=headers, json={
            "message": "I need an outfit for a wedding.",
            "session_id": "test_session",
            "language": "en"
        })
        if chat_resp.status_code != 200:
            print("Voice chat failed:", chat_resp.text)
            return
        print("Voice chat success:", chat_resp.json()["reply_text"])
        
        # We need to trigger finalize. We can send a message "finalize"
        print("3.5 Voice Chat Finalize Intent")
        chat_resp2 = await client.post(f"{API_URL}/api/v1/voice/converse-text", headers=headers, json={
            "message": "Finalize this outfit.",
            "session_id": "test_session",
            "language": "en"
        })
        print("Finalize intent response:", chat_resp2.json()["reply_text"])
        
        print("4. Finalize POST")
        fin_resp = await client.post(f"{API_URL}/api/v1/voice/finalize", headers=headers, json={
            "session_id": "test_session"
        })
        if fin_resp.status_code != 200:
            print("Finalize failed:", fin_resp.text)
            return
        print("Finalize success, Wardrobe ID:", fin_resp.json().get("wardrobe_item_id"))
        
if __name__ == "__main__":
    asyncio.run(test_flow())
