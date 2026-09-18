from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    document: str
    category: str
    chunk_index: int
    content: str
    fused_score: float
    rerank_score: float


class RetrievalResult(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
