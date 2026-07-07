import asyncio
from services.retrieval.web_search import search_products

async def run():
    res = await search_products({'garment_type': 'sherwani'}, limit=5)
    for p in res:
        print(p["url"])

if __name__ == "__main__":
    asyncio.run(run())
