import asyncio
import os
from gradio_client import Client, handle_file

async def test_real_image():
    img_path = r"d:\Aura-gem\fashion-ai\apps\mobile\assets\images\default_avatar.png"
    
    def run_vton():
        try:
            client = Client("yisol/IDM-VTON")
            result = client.predict(
                dict={"background": handle_file(img_path), "layers": [], "composite": None},
                garm_img=handle_file(img_path),
                garment_des="fashion outfit",
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=20,
                seed=42,
                api_name="/tryon"
            )
            print("VTON successful!")
            res_path = result[0]
            print(f"Res path: {res_path}")
            return True
        except Exception as e:
            print(f"IDM-VTON failed: {e}")
            return False

    await asyncio.to_thread(run_vton)

if __name__ == "__main__":
    asyncio.run(test_real_image())
