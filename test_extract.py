import asyncio
from services.agent.master import extract_params_llm

async def run():
    params = await extract_params_llm("i am a man generate an outfit for my friends wedding", "en", "neutral")
    print("GARMENT_TYPES:", params.garment_types)

if __name__ == "__main__":
    asyncio.run(run())
