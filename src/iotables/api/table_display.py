from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.session import get_database_session
from iotables.modules.ordering.table_presence import TablePresenceService

router = APIRouter(prefix="/table-display", tags=["Table Display"])


class QrTokenPayloadResponse(BaseModel):
    qr_token: str = Field(alias="qrToken")
    expires_at: str = Field(alias="expiresAt")
    refresh_after_seconds: int = Field(alias="refreshAfterSeconds")


def get_table_display_presence_service(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> TablePresenceService:
    return TablePresenceService(session)


@router.get("/qr-token", response_model=QrTokenPayloadResponse)
async def issue_qr_token(
    service: Annotated[
        TablePresenceService,
        Depends(get_table_display_presence_service),
    ],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    credential = display_credential_from_authorization(authorization)
    return (await service.issue_current_qr_token(display_credential=credential)).as_api_payload()


def display_credential_from_authorization(authorization: str | None) -> str:
    if authorization is None:
        raise display_not_authenticated()
    scheme, _, credential = authorization.partition(" ")
    if scheme != "DisplayCredential" or not credential.strip():
        raise display_not_authenticated()
    return credential.strip()


def display_not_authenticated() -> ApiError:
    return ApiError(
        status_code=401,
        code="display_not_authenticated",
        message="Display credential is invalid.",
    )
