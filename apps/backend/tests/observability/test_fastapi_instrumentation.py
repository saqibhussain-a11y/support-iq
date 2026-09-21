import pytest
from httpx import ASGITransport, AsyncClient
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.main import app


@pytest.mark.asyncio
async def test_health_request_emits_an_http_server_span():
    exporter = InMemorySpanExporter()
    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    server_spans = [
        s for s in exporter.get_finished_spans() if s.attributes.get("http.route") == "/health"
    ]
    assert len(server_spans) == 1
    assert server_spans[0].attributes["http.status_code"] == 200
    assert server_spans[0].attributes["http.method"] == "GET"
