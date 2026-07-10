import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.config import get_settings
from iotables.database.schema import (
    table_display_credentials,
    table_display_firmware_packages,
    tenants,
    venue_tables,
)
from iotables.security.context import ActorContext

FIRMWARE_TEMPLATE_PATH = Path("firmware/table-display/masa000.ino")
FIRMWARE_DOWNLOAD_TTL = timedelta(minutes=10)
DISPLAY_CREDENTIAL_BYTES = 32
DOWNLOAD_TOKEN_BYTES = 32


@dataclass(frozen=True)
class DisplayFirmwareCreated:
    firmware_id: UUID
    file_name: str
    credential_id: UUID
    table_id: UUID
    expires_at: datetime
    firmware_content: str

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "firmwareId": str(self.firmware_id),
            "fileName": self.file_name,
            "credentialId": str(self.credential_id),
            "tableId": str(self.table_id),
            "expiresAt": self.expires_at.isoformat(),
            "firmwareContent": self.firmware_content,
        }


@dataclass(frozen=True)
class DisplayFirmwareCommand:
    wifi_ssid: str
    wifi_password: str


class TableDisplayProvisioningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def generate_firmware(
        self,
        *,
        actor: ActorContext,
        table_id: UUID,
        command: DisplayFirmwareCommand,
    ) -> DisplayFirmwareCreated:
        tenant_id = require_tenant_id(actor)
        if not command.wifi_ssid.strip() or not command.wifi_password:
            raise wifi_required()

        table_row = await self._load_physical_table(tenant_id=tenant_id, table_id=table_id)
        if table_row is None:
            raise not_found_or_hidden()
        tenant_row = await self._load_tenant(tenant_id=tenant_id)
        if tenant_row is None:
            raise not_found_or_hidden()

        now = utc_now()
        credential_id = uuid4()
        firmware_id = uuid4()
        raw_credential = secrets.token_urlsafe(DISPLAY_CREDENTIAL_BYTES)
        file_name = f"masa{table_row['table_number']}.ino"
        expires_at = now + FIRMWARE_DOWNLOAD_TTL
        firmware_content = render_firmware(
            wifi_ssid=command.wifi_ssid.strip(),
            wifi_password=command.wifi_password,
            display_credential=raw_credential,
            tenant_host=tenant_host(tenant_row["subdomain"]),
            table_label=table_row["name"],
        )
        try:
            await self.session.execute(
                update(table_display_credentials)
                .where(
                    table_display_credentials.c.tenant_id == tenant_id,
                    table_display_credentials.c.table_id == table_id,
                    table_display_credentials.c.status == "active",
                )
                .values(status="revoked", revoked_at=now)
            )
            await self.session.execute(
                insert(table_display_credentials).values(
                    id=credential_id,
                    tenant_id=tenant_id,
                    table_id=table_id,
                    credential_hash=hash_secret(raw_credential),
                    status="active",
                    provisioned_at=now,
                    revoked_at=None,
                    last_seen_at=None,
                )
            )
            await self.session.execute(
                insert(table_display_firmware_packages).values(
                    id=firmware_id,
                    tenant_id=tenant_id,
                    table_id=table_id,
                    credential_id=credential_id,
                    file_name=file_name,
                    encrypted_firmware_ref=f"inline-one-time-response:{firmware_id}",
                    download_token_hash=hash_secret(secrets.token_urlsafe(DOWNLOAD_TOKEN_BYTES)),
                    generated_by_user_id=actor.user_id,
                    expires_at=expires_at,
                    downloaded_at=now,
                    created_at=now,
                )
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return DisplayFirmwareCreated(
            firmware_id=firmware_id,
            file_name=file_name,
            credential_id=credential_id,
            table_id=table_id,
            expires_at=expires_at,
            firmware_content=firmware_content,
        )

    async def _load_physical_table(self, *, tenant_id: UUID, table_id: UUID):
        return (
            (
                await self.session.execute(
                    select(venue_tables).where(
                        venue_tables.c.tenant_id == tenant_id,
                        venue_tables.c.id == table_id,
                        venue_tables.c.enabled.is_(True),
                        venue_tables.c.mode == "physical",
                    )
                )
            )
            .mappings()
            .first()
        )

    async def _load_tenant(self, *, tenant_id: UUID):
        return (
            (await self.session.execute(select(tenants).where(tenants.c.id == tenant_id)))
            .mappings()
            .first()
        )


def render_firmware(
    *,
    wifi_ssid: str,
    wifi_password: str,
    display_credential: str,
    tenant_host: str,
    table_label: str,
) -> str:
    template = FIRMWARE_TEMPLATE_PATH.read_text(encoding="utf-8")
    settings = get_settings()
    root_ca = getattr(settings, "table_display_root_ca_pem", "").strip()
    return (
        template.replace("__IOTABLES_WIFI_SSID__", c_string(wifi_ssid))
        .replace("__IOTABLES_WIFI_PASSWORD__", c_string(wifi_password))
        .replace("__IOTABLES_DISPLAY_CREDENTIAL__", c_string(display_credential))
        .replace("__IOTABLES_TENANT_HOST__", c_string(tenant_host))
        .replace("__IOTABLES_TABLE_LABEL__", c_string(table_label))
        .replace("__IOTABLES_TLS_ROOT_CA_PEM__", root_ca)
    )


def tenant_host(subdomain: str) -> str:
    root_domain = get_settings().tenant_root_domains[0]
    return f"{subdomain}.{root_domain}"


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def c_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def require_tenant_id(actor: ActorContext) -> UUID:
    if actor.tenant_id is None:
        raise ApiError(
            status_code=403,
            code="wrong_scope",
            message="This session is not bound to a tenant.",
        )
    return actor.tenant_id


def utc_now() -> datetime:
    return datetime.now(UTC)


def wifi_required() -> ApiError:
    return ApiError(status_code=422, code="wifi_required", message="WiFi fields are required.")


def not_found_or_hidden() -> ApiError:
    return ApiError(
        status_code=404,
        code="not_found_or_hidden",
        message="Resource was not found.",
    )
