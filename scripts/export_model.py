#!/usr/bin/env python3
"""Export finetuned model to GGUF/Ollama Modelfile (run after Colab training)."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to merged HF model dir")
    parser.add_argument("--output", default="models/exports", help="Export directory")
    parser.add_argument("--formats", default="gguf", help="Comma-separated: gguf,awq")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    modelfile = out / "Modelfile"
    modelfile.write_text(
        f"FROM {args.input}\nPARAMETER temperature 0.4\nSYSTEM You are a Telugu fashion stylist.\n",
        encoding="utf-8",
    )
    print(f"Wrote Ollama Modelfile: {modelfile}")
    print("Run: ollama create fashion-ai -f", modelfile)


if __name__ == "__main__":
    main()
