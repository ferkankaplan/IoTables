from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.platform.models import Tenant
from iotables.platform.repository import TenantRepository
from iotables.platform.schemas import TenantCreate


class TenantService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tenants = TenantRepository(session)

    async def list_tenants(self) -> list[Tenant]:
        return await self.tenants.list()

    async def create_tenant(self, payload: TenantCreate) -> Tenant:
        existing = await self.tenants.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant slug already exists.",
            )

        tenant = await self.tenants.add(Tenant(name=payload.name, slug=payload.slug))
        await self.session.commit()
        return tenant
