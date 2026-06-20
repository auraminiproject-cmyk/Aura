#!/usr/bin/env python3
"""DeepEval fashion benchmarks — run after model training."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


REGRESSION_CASES = [
    {"input": "wedding red lehenga 5000 hyderabad", "language": "te"},
    {"input": "office wear blue kurta", "language": "en"},
    {"input": "hello", "language": "te"},
]


async def run_regression() -> bool:
    from services.agent.master import run_fashion_agent

    passed = 0
    for case in REGRESSION_CASES:
        result = await run_fashion_agent(case["input"], language=case["language"])
        if result.get("reply"):
            passed += 1
    print(f"Regression: {passed}/{len(REGRESSION_CASES)} passed")
    return passed == len(REGRESSION_CASES)


def main() -> int:
    try:
        import deepeval  # noqa: F401

        print("DeepEval installed — add G-EVAL metrics in CI when models are finetuned")
    except ImportError:
        print("DeepEval not installed — pip install deepeval for full eval pipeline")
    ok = asyncio.run(run_regression())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
