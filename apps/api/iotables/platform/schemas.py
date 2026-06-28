import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from iotables.platform.models import TenantStatus


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TenantRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
