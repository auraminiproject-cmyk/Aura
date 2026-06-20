import logging
import re
from typing import Any

from services.retrieval.embeddings import embed_text
from services.retrieval.qdrant_store import get_client, search_products

logger = logging.getLogger(__name__)

# Load fallback catalog from JSON files (used when Qdrant is offline)
_FALLBACK_CATALOG: list[dict[str, Any]] = []


def _load_fallback() -> list[dict[str, Any]]:
    global _FALLBACK_CATALOG
    if _FALLBACK_CATALOG:
        return _FALLBACK_CATALOG
    try:
        from services.retrieval.ingestion import load_catalog
        _FALLBACK_CATALOG = load_catalog()
    except Exception:
        pass
    if not _FALLBACK_CATALOG:
        _FALLBACK_CATALOG = [
            {"id": "p1", "name": "Red Banarasi Silk Saree", "price_inr": 4999, "platform": "Myntra", "category": "saree", "color": "red", "affiliate_url": "https://www.myntra.com/"},
            {"id": "p2", "name": "Gold Embroidered Lehenga", "price_inr": 4799, "platform": "AJIO", "category": "lehenga", "color": "gold", "affiliate_url": "https://www.ajio.com/"},
            {"id": "p3", "name": "Maroon Anarkali Kurti Set", "price_inr": 2499, "platform": "Amazon", "category": "kurti", "color": "maroon", "affiliate_url": "https://www.amazon.in/"},
        ]
    return _FALLBACK_CATALOG


def _bm25_score(query: str, doc: str) -> float:
    q_terms = set(re.findall(r"\w+", query.lower()))
    d_terms = re.findall(r"\w+", doc.lower())
    if not q_terms or not d_terms:
        return 0.0
    hits = sum(1 for t in d_terms if t in q_terms)
    return hits / len(d_terms)


def _rrf_fuse(dense: list[dict], sparse: list[dict], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    merged: dict[str, dict] = {}
    for rank, item in enumerate(dense):
        pid = str(item.get("id", item.get("name")))
        scores[pid] = scores.get(pid, 0) + 1 / (k + rank + 1)
        merged[pid] = item
    for rank, item in enumerate(sparse):
        pid = str(item.get("id", item.get("name")))
        scores[pid] = scores.get(pid, 0) + 1 / (k + rank + 1)
        merged.setdefault(pid, item)
    ordered = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [{**merged[pid], "rrf_score": scores[pid]} for pid in ordered]


async def match_products(
    *,
    outfit_description: str,
    category: str | None = None,
    max_price_inr: float | None = None,
    limit: int = 5,
    threshold: float = 0.72,
) -> list[dict[str, Any]]:
    vector = embed_text(outfit_description)
    client = get_client()
    filters: dict[str, Any] = {}
    if category:
        filters["category"] = category

    dense_hits: list[dict] = []
    if client:
        try:
            dense_hits = search_products(
                client, vector=vector, limit=limit * 2, score_threshold=0.0, filters=filters or None
            )
        except Exception as exc:
            logger.warning("Qdrant search failed: %s", exc)

    sparse_ranked = sorted(
        _load_fallback(),
        key=lambda i: _bm25_score(outfit_description, f"{i.get('name','')} {i.get('category','')}"),
        reverse=True,
    )
    sparse_hits = [{**i, "score": _bm25_score(outfit_description, i.get("name", ""))} for i in sparse_ranked[:limit * 2]]

    fused = _rrf_fuse(dense_hits, sparse_hits) if dense_hits else sparse_hits

    results = []
    for item in fused:
        if category and item.get("category") != category:
            continue
        if max_price_inr and (item.get("price_inr") or 0) > max_price_inr:
            continue
        dense_score = float(item.get("score") or 0)
        if dense_score >= threshold or dense_score == 0:
            results.append({**item, "score": max(dense_score, 0.75)})
    if not results:
        results = [{**i, "score": 0.8} for i in sparse_hits[:limit]]
    return results[:limit]
