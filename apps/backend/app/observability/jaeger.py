import httpx

from app.core.config import get_settings
from app.observability.schemas import SpanOut, TraceOut


class TracingBackendUnavailable(Exception):
    pass


def parse_jaeger_trace(trace_id: str, payload: dict) -> TraceOut | None:
    traces = payload.get("data") or []
    if not traces:
        return None
    raw_spans = traces[0].get("spans") or []
    if not raw_spans:
        return None

    trace_start = min(span["startTime"] for span in raw_spans)
    trace_end = max(span["startTime"] + span["duration"] for span in raw_spans)

    spans = []
    for span in sorted(raw_spans, key=lambda s: s["startTime"]):
        parent_id = next(
            (ref["spanID"] for ref in span.get("references", []) if ref.get("refType") == "CHILD_OF"),
            None,
        )
        spans.append(
            SpanOut(
                span_id=span["spanID"],
                parent_span_id=parent_id,
                name=span["operationName"],
                start_offset_ms=(span["startTime"] - trace_start) / 1000,
                duration_ms=span["duration"] / 1000,
                attributes={tag["key"]: tag["value"] for tag in span.get("tags", [])},
            )
        )

    return TraceOut(
        trace_id=trace_id,
        duration_ms=(trace_end - trace_start) / 1000,
        complete=any(span.parent_span_id is None for span in spans),
        spans=spans,
    )


async def fetch_trace(trace_id: str) -> TraceOut | None:
    try:
        async with httpx.AsyncClient(base_url=get_settings().jaeger_query_url, timeout=5.0) as client:
            response = await client.get(f"/api/traces/{trace_id}")
    except httpx.HTTPError as exc:
        raise TracingBackendUnavailable(str(exc)) from exc
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise TracingBackendUnavailable(f"Jaeger returned {response.status_code}")
    return parse_jaeger_trace(trace_id, response.json())
