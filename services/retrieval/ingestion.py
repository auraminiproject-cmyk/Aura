"""Product catalog ingestion — JSON/CSV (no scraping; affiliate APIs preferred per blueprint).

Loads from multiple catalog files under data/catalog/ and ingests into Qdrant
with FashionCLIP embeddings for hybrid (dense + sparse) retrieval.
"""

import json
import logging
from pathlib import Path

from services.retrieval.embeddings import embed_text
from services.retrieval.qdrant_store import get_client, upsert_product

logger = logging.getLogger(__name__)

CATALOG_DIR = Path(__file__).resolve().parents[2] / "data" / "catalog"


def load_catalog(path: Path | None = None) -> list[dict]:
    """Load product catalog from a single file or all JSON files in catalog dir."""
    if path and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))

    # Load all JSON files in catalog directory
    all_products: list[dict] = []
    if CATALOG_DIR.is_dir():
        for f in sorted(CATALOG_DIR.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    all_products.extend(data)
                    logger.info("Loaded %d products from %s", len(data), f.name)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", f.name, exc)
    return all_products


def ingest_catalog(path: Path | None = None) -> int:
    """Embed and upsert products into Qdrant."""
    products = load_catalog(path)
    if not products:
        logger.info("No catalog products found")
        return 0

    client = get_client()
    if not client:
        logger.warning("Qdrant unavailable — catalog kept in JSON only (%d products)", len(products))
        return 0

    count = 0
    for item in products:
        # Build rich text for embedding: name + category + color + fabric + occasion + region
        text_parts = [
            item.get("name", ""),
            item.get("category", ""),
            item.get("color", ""),
            item.get("fabric", ""),
            item.get("occasion", ""),
            item.get("region", ""),
        ]
        text = " ".join(p for p in text_parts if p)
        vector = embed_text(text)
        upsert_product(client, vector=vector, payload=item)
        count += 1

    logger.info("Ingested %d products into Qdrant", count)
    return count
