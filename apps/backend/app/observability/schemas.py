from pydantic import BaseModel


class SpanOut(BaseModel):
    span_id: str
    parent_span_id: str | None
    name: str
    start_offset_ms: float
    duration_ms: float
    attributes: dict[str, str | int | float | bool]


class TraceOut(BaseModel):
    trace_id: str
    duration_ms: float
    complete: bool
    spans: list[SpanOut]
