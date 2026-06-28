from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.core.database import get_session
from iotables.platform.schemas import TenantCreate, TenantRead
from iotables.platform.service import TenantService

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/tenants", response_model=list[TenantRead])
async def list_tenants(session: AsyncSession = Depends(get_session)) -> list[TenantRead]:
    return await TenantService(session).list_tenants()


@router.post("/tenants", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    session: AsyncSession = Depends(get_session),
) -> TenantRead:
    return await TenantService(session).create_tenant(payload)
