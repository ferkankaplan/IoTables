from fastapi import APIRouter

from iotables.api.audit import router as audit_router
from iotables.api.auth import router as auth_router
from iotables.api.health import router as health_router
from iotables.api.platform import router as platform_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(platform_router)
