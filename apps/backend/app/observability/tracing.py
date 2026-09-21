import os

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Tracer

from app.core.config import get_settings

_configured = False
_langsmith_configured = False


def configure_tracing(service_name: str = "supportiq-backend") -> None:
    global _configured
    if _configured:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _configured = True


def get_tracer() -> Tracer:
    return trace.get_tracer("supportiq")


def configure_langsmith() -> None:
    global _langsmith_configured
    if _langsmith_configured:
        return
    _langsmith_configured = True

    settings = get_settings()
    if not (settings.langsmith_tracing and settings.langsmith_api_key):
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
