import asyncio
import base64
import os
import tempfile
from gradio_client import Client, handle_file

def get_b64_dummy():
    # 1x1 black pixel base64
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="

async def test_vton():
    user_b64 = get_b64_dummy()
    outfit_b64 = get_b64_dummy()
    
    def run_vton():
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_user:
                f_user.write(base64.b64decode(user_b64))
                user_path = f_user.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_outfit:
                f_outfit.write(base64.b64decode(outfit_b64))
                outfit_path = f_outfit.name
                
            print(f"User path: {user_path}")
            print(f"Outfit path: {outfit_path}")
            client = Client("yisol/IDM-VTON")
            result = client.predict(
                dict={"background": handle_file(user_path), "layers": [], "composite": None},
                garm_img=handle_file(outfit_path),
                garment_des="fashion outfit",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=20,
                seed=42,
                api_name="/tryon"
            )
            print("VTON successful!")
            res_path = result[0]
            os.remove(user_path)
            os.remove(outfit_path)
            return True
        except Exception as e:
            print(f"IDM-VTON failed: {e}")
            return False

    res = await asyncio.to_thread(run_vton)
    print(f"Result: {res}")

if __name__ == "__main__":
    asyncio.run(test_vton())
