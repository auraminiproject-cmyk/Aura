"""Qdrant — use local Docker (see docker-compose). Skip Qdrant Cloud unless verified no card."""

import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)
COLLECTION = "fashion_products"
VECTOR_SIZE = 512


def get_client() -> QdrantClient | None:
    settings = get_settings()
    try:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    except Exception as exc:
        logger.warning("Qdrant unavailable: %s", exc)
        return None


def ensure_collection(client: QdrantClient) -> None:
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE),
            hnsw_config=qmodels.HnswConfigDiff(m=32, ef_construct=200),
        )
        for field in ("category", "platform", "color", "brand"):
            try:
                client.create_payload_index(COLLECTION, field_name=field, field_schema=qmodels.PayloadSchemaType.KEYWORD)
            except Exception:
                pass


def upsert_product(client: QdrantClient, *, vector: list[float], payload: dict[str, Any]) -> str:
    ensure_collection(client)
    raw_id = payload.get("id")
    if raw_id:
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id)))
    else:
        point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION,
        points=[qmodels.PointStruct(id=point_id, vector=vector, payload=payload)],
    )
    return point_id


def search_products(
    client: QdrantClient,
    *,
    vector: list[float],
    limit: int = 5,
    score_threshold: float = 0.72,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ensure_collection(client)
    qfilter = None
    if filters:
        must = []
        for key, val in filters.items():
            must.append(qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=val)))
        qfilter = qmodels.Filter(must=must)

    results = client.search(
        collection_name=COLLECTION,
        query_vector=vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=qfilter,
    )
    return [{"id": r.id, "score": r.score, **(r.payload or {})} for r in results]
