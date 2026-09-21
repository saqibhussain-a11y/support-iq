from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.health import router as health_router
from app.api.tickets import router as tickets_router
from app.core.config import get_settings
from app.observability.tracing import configure_tracing

settings = get_settings()
configure_tracing()

app = FastAPI(title="SupportIQ API", version="0.1.0")
FastAPIInstrumentor.instrument_app(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tickets_router)
