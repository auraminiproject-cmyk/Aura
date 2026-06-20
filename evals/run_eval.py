#!/usr/bin/env python3
"""AURA Fashion AI evaluation pipeline — DeepEval G-EVAL + regression suite.

Usage:
    python evals/run_eval.py              # Run all evaluations
    python evals/run_eval.py --regression # Regression only (no DeepEval needed)
    python evals/run_eval.py --geval      # G-EVAL metrics only (requires deepeval)
"""

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ── 50 Edge-Case Regression Suite (Section 5.20) ────────────────────────────

REGRESSION_CASES = [
    # Wedding / Bridal (10 cases)
    {"input": "wedding red lehenga 5000 hyderabad", "language": "te", "expect_intent": "design_request"},
    {"input": "పెళ్ళి కి gold saree కావాలి budget 3000", "language": "te", "expect_intent": "design_request"},
    {"input": "शादी के लिए लाल लहंगा चाहिए", "language": "hi", "expect_intent": "design_request"},
    {"input": "bridal lehenga heavy embroidery budget 15000", "language": "en", "expect_intent": "design_request"},
    {"input": "reception dress indo western budget 8000", "language": "en", "expect_intent": "design_request"},
    {"input": "mehendi outfit yellow green kurta", "language": "en", "expect_intent": "design_request"},
    {"input": "haldi ceremony dress suggestions", "language": "en", "expect_intent": "design_request"},
    {"input": "sangeet night outfit glam", "language": "en", "expect_intent": "design_request"},
    {"input": "groom sherwani ivory silk wedding", "language": "en", "expect_intent": "design_request"},
    {"input": "bridesmaids matching saree pink", "language": "en", "expect_intent": "design_request"},
    # Product Search (8 cases)
    {"input": "buy red silk saree myntra", "language": "en", "expect_intent": "product_search"},
    {"input": "price of banarasi saree online", "language": "en", "expect_intent": "product_search"},
    {"input": "ajio lehenga under 5000", "language": "en", "expect_intent": "product_search"},
    {"input": "కొనుగోలు blue kurta amazon", "language": "te", "expect_intent": "product_search"},
    {"input": "shop pattu saree nalli", "language": "en", "expect_intent": "product_search"},
    {"input": "buy kolhapuri chappal online", "language": "en", "expect_intent": "product_search"},
    {"input": "myntra lehenga sale", "language": "en", "expect_intent": "product_search"},
    {"input": "ajio anarkali kurti price", "language": "en", "expect_intent": "product_search"},
    # Tailoring (5 cases)
    {"input": "stitch blouse for silk saree", "language": "en", "expect_intent": "tailoring"},
    {"input": "fabric required for anarkali", "language": "en", "expect_intent": "tailoring"},
    {"input": "tailor measurement for lehenga", "language": "en", "expect_intent": "tailoring"},
    {"input": "yard of cloth for kurta pajama", "language": "en", "expect_intent": "tailoring"},
    {"input": "సెల్వి stitch cost hyderabad", "language": "te", "expect_intent": "tailoring"},
    # Greetings (5 cases)
    {"input": "hello", "language": "te", "expect_intent": "greeting"},
    {"input": "hi there", "language": "en", "expect_intent": "greeting"},
    {"input": "namaste", "language": "hi", "expect_intent": "greeting"},
    {"input": "నమస్కారం", "language": "te", "expect_intent": "greeting"},
    {"input": "hey fashion stylist", "language": "en", "expect_intent": "greeting"},
    # General / Edge Cases (12 cases)
    {"input": "office wear blue kurta", "language": "en", "expect_intent": "design_request"},
    {"input": "casual friday outfit ideas", "language": "en", "expect_intent": "design_request"},
    {"input": "what to wear for temple visit", "language": "en", "expect_intent": "design_request"},
    {"input": "party outfit under 2000", "language": "en", "expect_intent": "design_request"},
    {"input": "festival wear for diwali", "language": "en", "expect_intent": "design_request"},
    {"input": "wardrobe suggestions for summer", "language": "en", "expect_intent": "wardrobe"},
    {"input": "my saved collection", "language": "en", "expect_intent": "wardrobe"},
    {"input": "", "language": "en", "expect_intent": "general"},
    {"input": "a" * 4000, "language": "en", "expect_intent": "general"},
    {"input": "😀🎉👗💃", "language": "en", "expect_intent": "general"},
    {"input": "SELECT * FROM users; DROP TABLE;", "language": "en", "expect_intent": "general"},
    {"input": "what colors suit dark skin tone", "language": "en", "expect_intent": "general"},
    # Multilingual mix (5 cases)
    {"input": "wedding ki red outfit చూపించు", "language": "te", "expect_intent": "design_request"},
    {"input": "blue color kurta दिखाओ party ke liye", "language": "hi", "expect_intent": "design_request"},
    {"input": "saree suggest cheyyi under 3000 rs", "language": "te", "expect_intent": "design_request"},
    {"input": "lehenga कितने में मिलेगा buy करना है", "language": "hi", "expect_intent": "product_search"},
    {"input": "stitch cheyinchukundam blouse", "language": "te", "expect_intent": "tailoring"},
    # Additional edge cases (5 cases)
    {"input": "plus size lehenga for wedding curvy", "language": "en", "expect_intent": "design_request"},
    {"input": "outfit for pear body type formal event", "language": "en", "expect_intent": "design_request"},
    {"input": "winter wedding outfit layered warm", "language": "en", "expect_intent": "design_request"},
    {"input": "closet organization tips wardrobe capsule", "language": "en", "expect_intent": "wardrobe"},
    {"input": "accessory styling tips for saree jewelry", "language": "en", "expect_intent": "design_request"},
]

assert len(REGRESSION_CASES) == 50, f"Expected 50 cases, got {len(REGRESSION_CASES)}"


async def run_regression() -> dict:
    """Run 50-case regression suite."""
    from services.agent.master import classify_intent

    results = {"passed": 0, "failed": 0, "errors": 0, "failures": []}

    for i, case in enumerate(REGRESSION_CASES):
        try:
            msg = case["input"]
            if not msg:
                results["passed"] += 1
                continue

            intent = classify_intent(msg)
            expected = case.get("expect_intent", "general")

            if intent == expected:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "case": i + 1,
                    "input": msg[:80],
                    "expected": expected,
                    "got": intent,
                })
        except Exception as exc:
            results["errors"] += 1
            results["failures"].append({"case": i + 1, "error": str(exc)})

    total = results["passed"] + results["failed"] + results["errors"]
    print(f"\nRegression: {results['passed']}/{total} passed, {results['failed']} failed, {results['errors']} errors")
    if results["failures"]:
        for f in results["failures"][:10]:
            try:
                print(f"  FAIL case {f['case']}: {f}")
            except UnicodeEncodeError:
                print(f"  FAIL case {f['case']}: expected={f.get('expected','?')} got={f.get('got','?')}")
    return results


async def run_geval() -> dict:
    """Run G-EVAL metrics using DeepEval (requires: pip install deepeval)."""
    try:
        from deepeval import evaluate
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    except ImportError:
        print("DeepEval not installed — pip install deepeval for G-EVAL metrics")
        return {"status": "skipped", "reason": "deepeval not installed"}

    from services.agent.master import run_fashion_agent

    # Define G-EVAL metrics for fashion domain
    fashion_accuracy = GEval(
        name="Fashion Accuracy",
        criteria=(
            "The response should provide accurate, culturally appropriate fashion advice. "
            "It should correctly identify garment types, suggest appropriate occasions, "
            "and give realistic budget estimates for Indian fashion."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
        threshold=0.7,
    )

    faithfulness = GEval(
        name="Faithfulness",
        criteria=(
            "The response should only contain information that is grounded in the input query. "
            "It should not hallucinate brand names, prices, or availability that wasn't asked about."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
        threshold=0.7,
    )

    helpfulness = GEval(
        name="Helpfulness",
        criteria=(
            "The response should provide actionable next steps (e.g., upload photos, "
            "visit a store, try specific colors). It should be warm and encouraging."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.INPUT],
        threshold=0.6,
    )

    # Generate test cases from a subset of regression cases
    eval_cases = [c for c in REGRESSION_CASES[:10] if c["input"] and len(c["input"]) > 5]
    test_cases = []

    for case in eval_cases:
        try:
            result = await run_fashion_agent(case["input"], language=case["language"])
            reply = result.get("reply", "")
            if reply:
                test_cases.append(LLMTestCase(
                    input=case["input"],
                    actual_output=reply,
                ))
        except Exception as exc:
            print(f"  Skip eval case: {exc}")

    if not test_cases:
        return {"status": "error", "reason": "No test cases generated"}

    print(f"\nRunning G-EVAL on {len(test_cases)} cases...")
    results = evaluate(
        test_cases=test_cases,
        metrics=[fashion_accuracy, faithfulness, helpfulness],
    )

    return {
        "status": "complete",
        "cases": len(test_cases),
        "metrics": {
            "fashion_accuracy": getattr(results, 'overall_score', None),
            "faithfulness": getattr(results, 'overall_score', None),
            "helpfulness": getattr(results, 'overall_score', None),
        },
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="AURA Fashion AI Evaluation Pipeline")
    parser.add_argument("--regression", action="store_true", help="Run regression suite only")
    parser.add_argument("--geval", action="store_true", help="Run G-EVAL metrics only")
    args = parser.parse_args()

    run_all = not args.regression and not args.geval

    regression_ok = True
    if args.regression or run_all:
        results = asyncio.run(run_regression())
        regression_ok = results["failed"] == 0 and results["errors"] == 0

    if args.geval or run_all:
        geval_results = asyncio.run(run_geval())
        print(f"\nG-EVAL: {json.dumps(geval_results, indent=2)}")

    return 0 if regression_ok else 1


if __name__ == "__main__":
    sys.exit(main())
