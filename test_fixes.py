import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from services.agent.master import extract_params_llm
from services.agent.body_analyzer import analyze

async def main():
    history = [
        {"role": "user", "content": "I want a blue lehenga for a wedding"},
        {"role": "assistant", "content": "A blue lehenga would look stunning! Shall we finalize?"}
    ]
    print("--- Test 1: No history ---")
    params1 = await extract_params_llm("finalize", "en", "female", history=None)
    print(params1)
    
    print("--- Test 2: With history ---")
    params2 = await extract_params_llm("finalize", "en", "female", history=history)
    print(params2)
    
    print("--- Test 3: Body Analyzer ---")
    measurements = {"height_cm": 165, "chest_cm": 88, "waist_cm": 70, "hip_cm": 96, "shoulder_cm": 40, "inseam_cm": 75}
    analysis = analyze(measurements)
    print(f"Body Type: {analysis.body_type}")

if __name__ == "__main__":
    asyncio.run(main())
