import logging

from services.retrieval.ingestion import ingest_catalog

logger = logging.getLogger(__name__)


def seed_product_catalog() -> None:
    """Seed Qdrant from data/catalog/products.json (no scraping)."""
    try:
        count = ingest_catalog()
        logger.info("Catalog ingestion: %d products", count)
    except Exception as exc:
        logger.warning("Product seed skipped: %s", exc)
