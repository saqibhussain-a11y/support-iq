from fastapi import APIRouter, HTTPException, Path

from app.observability.jaeger import TracingBackendUnavailable, fetch_trace
from app.observability.schemas import TraceOut

router = APIRouter(prefix="/api", tags=["traces"])


@router.get("/traces/{trace_id}", response_model=TraceOut)
async def get_trace(trace_id: str = Path(pattern=r"^[0-9a-f]{32}$")) -> TraceOut:
    try:
        trace = await fetch_trace(trace_id)
    except TracingBackendUnavailable as exc:
        raise HTTPException(status_code=503, detail="Tracing backend unavailable") from exc
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace
