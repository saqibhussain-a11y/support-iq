from fastapi import APIRouter
from pydantic import BaseModel

from app.db.session import ping_database

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    database: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    try:
        await ping_database()
        db_status = "ok"
    except Exception:
        db_status = "unavailable"

    return ReadinessResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
    )
