import pytest
from httpx import ASGITransport, AsyncClient

import app.api.traces as traces_module
from app.main import app
from app.observability.jaeger import TracingBackendUnavailable, parse_jaeger_trace
from app.observability.schemas import SpanOut, TraceOut

TRACE_ID = "b36ee8ce2ecbb2c45cafe579e39a2db3"


def jaeger_payload() -> dict:
    return {
        "data": [
            {
                "traceID": TRACE_ID,
                "spans": [
                    {
                        "spanID": "child",
                        "operationName": "workflow.classify",
                        "references": [{"refType": "CHILD_OF", "traceID": TRACE_ID, "spanID": "root"}],
                        "startTime": 1_000_500,
                        "duration": 1_200_000,
                        "tags": [{"key": "classification.category", "type": "string", "value": "account"}],
                    },
                    {
                        "spanID": "root",
                        "operationName": "POST /api/tickets/stream",
                        "references": [],
                        "startTime": 1_000_000,
                        "duration": 4_000_000,
                        "tags": [],
                    },
                ],
            }
        ]
    }


def test_parse_jaeger_trace_orders_spans_and_computes_relative_offsets():
    trace = parse_jaeger_trace(TRACE_ID, jaeger_payload())

    assert trace is not None
    assert [span.name for span in trace.spans] == ["POST /api/tickets/stream", "workflow.classify"]
    root, child = trace.spans
    assert root.parent_span_id is None
    assert root.start_offset_ms == 0
    assert child.parent_span_id == "root"
    assert child.start_offset_ms == 0.5
    assert child.duration_ms == 1200
    assert child.attributes == {"classification.category": "account"}
    assert trace.duration_ms == 4000
    assert trace.complete is True


def test_parse_jaeger_trace_is_incomplete_until_the_root_span_arrives():
    payload = jaeger_payload()
    payload["data"][0]["spans"] = [payload["data"][0]["spans"][0]]

    trace = parse_jaeger_trace(TRACE_ID, payload)

    assert trace is not None
    assert trace.complete is False


def test_parse_jaeger_trace_returns_none_for_an_empty_payload():
    assert parse_jaeger_trace(TRACE_ID, {"data": []}) is None
    assert parse_jaeger_trace(TRACE_ID, {"data": None}) is None


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


@pytest.mark.asyncio
async def test_trace_endpoint_returns_the_parsed_trace(monkeypatch):
    async def fake_fetch(trace_id: str) -> TraceOut:
        return TraceOut(
            trace_id=trace_id,
            duration_ms=10,
            complete=True,
            spans=[
                SpanOut(
                    span_id="root",
                    parent_span_id=None,
                    name="ticket.process",
                    start_offset_ms=0,
                    duration_ms=10,
                    attributes={},
                )
            ],
        )

    monkeypatch.setattr(traces_module, "fetch_trace", fake_fetch)

    response = await _get(f"/api/traces/{TRACE_ID}")

    assert response.status_code == 200
    assert response.json()["spans"][0]["name"] == "ticket.process"


@pytest.mark.asyncio
async def test_trace_endpoint_returns_404_when_the_trace_is_not_in_jaeger(monkeypatch):
    async def fake_fetch(trace_id: str) -> None:
        return None

    monkeypatch.setattr(traces_module, "fetch_trace", fake_fetch)

    response = await _get(f"/api/traces/{TRACE_ID}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_trace_endpoint_returns_503_when_jaeger_is_unreachable(monkeypatch):
    async def fake_fetch(trace_id: str) -> None:
        raise TracingBackendUnavailable("connection refused")

    monkeypatch.setattr(traces_module, "fetch_trace", fake_fetch)

    response = await _get(f"/api/traces/{TRACE_ID}")

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_trace_endpoint_rejects_a_malformed_trace_id():
    response = await _get("/api/traces/not-a-trace-id")

    assert response.status_code == 422
