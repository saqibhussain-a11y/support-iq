from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.observability.tracing import configure_tracing, current_trace_id, get_tracer


def test_configure_tracing_is_idempotent():
    configure_tracing()
    provider_first = trace.get_tracer_provider()

    configure_tracing()
    provider_second = trace.get_tracer_provider()

    assert provider_first is provider_second


def test_get_tracer_emits_spans_with_attributes():
    configure_tracing()
    exporter = InMemorySpanExporter()
    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))

    with get_tracer().start_as_current_span("test.tracing.span") as span:
        span.set_attribute("foo", "bar")

    matching = [s for s in exporter.get_finished_spans() if s.name == "test.tracing.span"]
    assert len(matching) == 1
    assert matching[0].attributes["foo"] == "bar"


def test_nested_spans_share_a_trace_id():
    configure_tracing()
    exporter = InMemorySpanExporter()
    trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(exporter))

    with get_tracer().start_as_current_span("test.tracing.outer"):
        with get_tracer().start_as_current_span("test.tracing.inner"):
            pass

    spans = {s.name: s for s in exporter.get_finished_spans()}
    outer = spans["test.tracing.outer"]
    inner = spans["test.tracing.inner"]
    assert inner.parent.trace_id == outer.context.trace_id


def test_current_trace_id_is_the_active_span_trace_id_as_32_char_hex():
    configure_tracing()

    with get_tracer().start_as_current_span("test.tracing.current") as span:
        trace_id = current_trace_id()

    assert trace_id == format(span.get_span_context().trace_id, "032x")
    assert len(trace_id) == 32


def test_current_trace_id_is_none_outside_any_span():
    configure_tracing()

    assert current_trace_id() is None
