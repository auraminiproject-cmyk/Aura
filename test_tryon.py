import asyncio
from services.vision.virtual_tryon import try_on_with_spaces

async def run():
    try:
        res = await try_on_with_spaces(open('test_body.jpg', 'rb').read(), open('test.png', 'rb').read())
        print('SUCCESS' if res else 'FAIL')
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(run())
