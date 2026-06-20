"""Seed Qdrant with sample products. Run: python scripts/seed_products.py"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.retrieval.product_match import _pseudo_embedding
from services.retrieval.qdrant_store import get_client, upsert_product

SAMPLES = [
    {
        "name": "Red Banarasi Silk Saree",
        "price_inr": 4999,
        "platform": "Myntra",
        "category": "saree",
        "color": "red",
        "affiliate_url": "https://www.myntra.com/",
    },
    {
        "name": "Gold Embroidered Lehenga",
        "price_inr": 4799,
        "platform": "AJIO",
        "category": "lehenga",
        "color": "gold",
        "affiliate_url": "https://www.ajio.com/",
    },
]


def main() -> None:
    client = get_client()
    if not client:
        print("Qdrant not available; skipping seed")
        return
    for item in SAMPLES:
        vec = _pseudo_embedding(item["name"])
        pid = upsert_product(client, vector=vec, payload=item)
        print(f"Seeded {pid}: {item['name']}")


if __name__ == "__main__":
    main()
