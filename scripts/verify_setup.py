#!/usr/bin/env python3
"""Verify zero-card local setup. Run: python scripts/verify_setup.py"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    print("Fashion AI setup verification\n")

    env_path = ROOT / ".env"
    check(".env exists", env_path.is_file(), "copy .env.example to .env")

    groq = os.getenv("GROQ_API_KEY", "")
    hf = os.getenv("HUGGINGFACE_API_KEY", "")
    check("GROQ_API_KEY set", bool(groq), "optional but needed for live LLM")
    check("HUGGINGFACE_API_KEY set", bool(hf), "optional for ASR/HF models")

    check("STORAGE_BACKEND not r2", "r2" not in os.getenv("STORAGE_BACKEND", "local").lower())

    try:
        from services.api.main import create_app

        app = create_app()
        check("FastAPI app loads", app is not None)
    except Exception as exc:
        check("FastAPI app loads", False, str(exc))

    try:
        from services.agent.graph import build_fashion_graph

        g = build_fashion_graph()
        check("LangGraph compiles", g is not None)
    except Exception as exc:
        check("LangGraph compiles", False, str(exc))

    failed = sum(1 for _, ok, _ in CHECKS if not ok)
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    # load .env if present
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
    sys.exit(main())
