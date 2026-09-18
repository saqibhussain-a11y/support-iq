from pydantic import BaseModel


class RawDocument(BaseModel):
    document: str
    category: str
    text: str


class DocumentChunk(BaseModel):
    document: str
    category: str
    source: str
    chunk_index: int
    content: str


class IndexingResult(BaseModel):
    documents_processed: int
    chunks_created: int
    chunks_embedded: int
    total_chunks_in_store: int
