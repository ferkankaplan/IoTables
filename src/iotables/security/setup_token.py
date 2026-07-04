import base64
import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken


class SetupTokenError(ValueError):
    pass


def issue_setup_token(
    *,
    encryption_key: str,
    user_id: UUID,
    tenant_id: UUID | None,
    app_scope: str,
    purpose: str,
    expires_at: datetime,
) -> str:
    payload = {
        "userId": str(user_id),
        "tenantId": str(tenant_id) if tenant_id is not None else None,
        "appScope": app_scope,
        "purpose": purpose,
        "expiresAt": expires_at.astimezone(UTC).isoformat(),
    }
    return _fernet(encryption_key).encrypt(json.dumps(payload).encode("utf-8")).decode("ascii")


def parse_setup_token(*, encryption_key: str, token: str) -> dict[str, object]:
    try:
        raw_payload = _fernet(encryption_key).decrypt(token.encode("ascii"))
        payload = json.loads(raw_payload.decode("utf-8"))
        expires_at = datetime.fromisoformat(str(payload["expiresAt"]))
        if expires_at <= datetime.now(UTC):
            raise SetupTokenError("setup token expired")
        return payload
    except (InvalidToken, KeyError, TypeError, ValueError) as exc:
        raise SetupTokenError("setup token invalid") from exc


def _fernet(encryption_key: str) -> Fernet:
    digest = hashlib.sha256(encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))
