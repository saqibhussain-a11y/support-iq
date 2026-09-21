import asyncio
import sys

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.db.session import session_scope
from app.workflows.dependencies import get_support_workflow_service

exporter = InMemorySpanExporter()
provider = TracerProvider(resource=Resource.create({"service.name": "supportiq-backend"}))
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)


async def main() -> None:
    message = " ".join(sys.argv[1:]) or (
        "I was charged twice for my subscription this month and I want a refund."
    )

    service = get_support_workflow_service()
    async with session_scope() as session:
        await service.run(session, message)

    spans = sorted(exporter.get_finished_spans(), key=lambda s: s.start_time)
    for span in spans:
        duration_ms = (span.end_time - span.start_time) / 1_000_000
        indent = "  " if span.parent is not None else ""
        print(f"{indent}{span.name}  ({duration_ms:.1f}ms)")
        for key, value in span.attributes.items():
            print(f"{indent}    {key} = {value}")


if __name__ == "__main__":
    asyncio.run(main())
