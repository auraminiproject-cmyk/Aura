import asyncio
import httpx
from test_vton import get_b64_dummy

async def test_idm_raw():
    user_b64 = get_b64_dummy()
    outfit_b64 = get_b64_dummy()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://yisol-idm-vton.hf.space/call/tryon",
            json={
                "data": [
                    {"background": f"data:image/png;base64,{user_b64}", "layers": [], "composite": None},
                    f"data:image/png;base64,{outfit_b64}",
                    "fashion outfit",
                    True,
                    False,
                    20,
                    42
                ]
            }
        )
        print(resp.status_code)
        print(resp.text)

if __name__ == "__main__":
    asyncio.run(test_idm_raw())
