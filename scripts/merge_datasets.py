import json
from pathlib import Path

base = Path("data/processed")
seed = json.loads((base / "fashion_vlm_sharegpt.json").read_text(encoding="utf-8"))
gen = json.loads((base / "fashion_conversations_clean.json").read_text(encoding="utf-8"))
merged = seed + gen
(base / "fashion_vlm_sharegpt.json").write_text(
    json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"{len(seed)} seed + {len(gen)} gen = {len(merged)} total conversations")
