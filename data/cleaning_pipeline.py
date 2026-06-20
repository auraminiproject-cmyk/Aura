"""Blueprint Section 5 — data cleaning DAG (dedup, quality, toxicity, format)."""

from dataclasses import dataclass
from typing import List


@dataclass
class CleaningConfig:
    min_tokens: int = 20
    max_tokens: int = 2000
    dedup_threshold: float = 0.85
    min_image_size: int = 512
    toxicity_threshold: float = 0.5


class DataCleaningPipeline:
    def __init__(self, config: CleaningConfig | None = None):
        self.config = config or CleaningConfig()

    def _token_count(self, entry: dict) -> int:
        text = entry.get("text") or entry.get("instruction") or entry.get("output") or ""
        return len(str(text).split())

    def clean_text_dataset(self, entries: List[dict]) -> List[dict]:
        entries = self._remove_duplicates(entries)
        entries = [e for e in entries if self.config.min_tokens <= self._token_count(e) <= self.config.max_tokens]
        return entries

    def _remove_duplicates(self, entries: List[dict]) -> List[dict]:
        seen = set()
        out = []
        for e in entries:
            key = (e.get("instruction") or "") + (e.get("output") or "") + (e.get("text") or "")
            h = hash(key)
            if h in seen:
                continue
            seen.add(h)
            out.append(e)
        return out

    def to_sharegpt(self, entries: List[dict]) -> List[dict]:
        formatted = []
        for e in entries:
            formatted.append(
                {
                    "conversations": [
                        {"from": "human", "value": e.get("instruction", e.get("input", ""))},
                        {"from": "gpt", "value": e.get("output", e.get("response", ""))},
                    ]
                }
            )
        return formatted
