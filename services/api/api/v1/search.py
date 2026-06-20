from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.api.core.security import get_current_user_id
from services.retrieval.product_match import match_products

router = APIRouter()


class ProductSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    category: str | None = None
    max_price_inr: float | None = None
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/products")
async def search_products(body: ProductSearchRequest, _user_id: str = Depends(get_current_user_id)):
    hits = await match_products(
        outfit_description=body.query,
        category=body.category,
        max_price_inr=body.max_price_inr,
        limit=body.limit,
    )
    return {"results": hits, "count": len(hits)}
