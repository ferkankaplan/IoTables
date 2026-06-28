from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.platform.models import Tenant


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Tenant]:
        result = await self.session.scalars(select(Tenant).order_by(Tenant.created_at.desc()))
        return list(result)

    async def get_by_slug(self, slug: str) -> Tenant | None:
        return await self.session.scalar(select(Tenant).where(Tenant.slug == slug))

    async def add(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.flush()
        return tenant
