from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from iotables.config import Settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


@router.get("/live", response_model=HealthResponse)
async def live(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
    )
