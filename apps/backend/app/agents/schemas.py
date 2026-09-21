from typing import Literal

from pydantic import BaseModel


class TicketClassification(BaseModel):
    category: Literal["billing", "shipping", "product", "account", "other"]
    priority: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "frustrated", "angry"]


class SupportResponse(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool
    top_rerank_score: float | None = None
    context: str = ""
