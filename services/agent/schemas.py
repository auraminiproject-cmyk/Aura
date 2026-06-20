from typing import Literal

from pydantic import BaseModel, Field


class DesignParams(BaseModel):
    occasion: str | None = None
    budget_inr: float | None = None
    colors: list[str] = Field(default_factory=list)
    body_type: str | None = None
    cultural_context: str | None = None
    garment_types: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    message: str
    language: str = "te"
    intent: Literal["greeting", "design_request", "product_search", "tailoring", "wardrobe", "general"] = "general"
    params: DesignParams = Field(default_factory=DesignParams)
    reply: str = ""
