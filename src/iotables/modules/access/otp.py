import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.api.errors import ApiError
from iotables.database.schema import message_deliveries, otp_attempts, otp_challenges

OTP_TTL = timedelta(minutes=5)
OTP_DIGITS = 6
MAX_ATTEMPTS = 5


@dataclass(frozen=True)
class OtpChallengeState:
    challenge_id: UUID
    target_hint: str
    expires_at: datetime
    remaining_attempts: int


class OtpMessagingService:
    def __init__(self, session: AsyncSession, secret_key: str) -> None:
        self.session = session
        self.secret_key = secret_key

    async def create_challenge(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        purpose: str,
        target_gsm: str,
        now: datetime,
    ) -> OtpChallengeState:
        active_challenge = await self._load_active_challenge(
            tenant_id=tenant_id,
            user_id=user_id,
            purpose=purpose,
            now=now,
        )
        if active_challenge is not None:
            attempt_count = await self._attempt_count(
                tenant_id=tenant_id,
                challenge_id=active_challenge["id"],
            )
            if attempt_count >= MAX_ATTEMPTS:
                raise ApiError(
                    status_code=429,
                    code="otp_locked",
                    message="OTP attempt limit exceeded.",
                )
            return OtpChallengeState(
                challenge_id=active_challenge["id"],
                target_hint=mask_gsm(active_challenge["target_gsm"]),
                expires_at=active_challenge["expires_at"],
                remaining_attempts=MAX_ATTEMPTS - attempt_count,
            )

        challenge_id = uuid4()
        code = _generate_code()
        expires_at = now + OTP_TTL
        await self.session.execute(
            insert(otp_challenges).values(
                id=challenge_id,
                tenant_id=tenant_id,
                user_id=user_id,
                purpose=purpose,
                target_gsm=target_gsm,
                code_hash=_hash_code(
                    secret_key=self.secret_key,
                    challenge_id=challenge_id,
                    code=code,
                ),
                expires_at=expires_at,
                created_at=now,
            )
        )
        await self.session.execute(
            insert(message_deliveries).values(
                id=uuid4(),
                tenant_id=tenant_id,
                otp_challenge_id=challenge_id,
                delivery_no=1,
                provider="sms",
                status="queued",
                created_at=now,
            )
        )
        return OtpChallengeState(
            challenge_id=challenge_id,
            target_hint=mask_gsm(target_gsm),
            expires_at=expires_at,
            remaining_attempts=MAX_ATTEMPTS,
        )

    async def _load_active_challenge(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        purpose: str,
        now: datetime,
    ):
        return (
            (
                await self.session.execute(
                    select(otp_challenges)
                    .where(
                        otp_challenges.c.tenant_id == tenant_id,
                        otp_challenges.c.user_id == user_id,
                        otp_challenges.c.purpose == purpose,
                        otp_challenges.c.expires_at > now,
                        otp_challenges.c.verified_at.is_(None),
                    )
                    .order_by(otp_challenges.c.created_at.desc())
                    .limit(1)
                )
            )
            .mappings()
            .first()
        )

    async def verify(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        challenge_id: UUID,
        purpose: str,
        code: str,
        now: datetime,
    ) -> None:
        challenge = (
            (
                await self.session.execute(
                    select(otp_challenges).where(
                        otp_challenges.c.tenant_id == tenant_id,
                        otp_challenges.c.id == challenge_id,
                        otp_challenges.c.user_id == user_id,
                        otp_challenges.c.purpose == purpose,
                    )
                )
            )
            .mappings()
            .first()
        )
        if challenge is None:
            raise _otp_invalid()
        if challenge["verified_at"] is not None:
            return

        attempt_count = await self._attempt_count(tenant_id=tenant_id, challenge_id=challenge_id)
        if attempt_count >= MAX_ATTEMPTS:
            raise ApiError(
                status_code=429,
                code="otp_locked",
                message="OTP attempt limit exceeded.",
            )
        if challenge["expires_at"] <= now:
            await self._append_attempt(
                tenant_id=tenant_id,
                challenge_id=challenge_id,
                attempt_no=attempt_count + 1,
                result="expired",
                now=now,
            )
            raise ApiError(
                status_code=410,
                code="otp_expired",
                message="OTP challenge has expired.",
            )

        submitted_hash = _hash_code(
            secret_key=self.secret_key,
            challenge_id=challenge_id,
            code=code,
        )
        if not hmac.compare_digest(submitted_hash, challenge["code_hash"]):
            await self._append_attempt(
                tenant_id=tenant_id,
                challenge_id=challenge_id,
                attempt_no=attempt_count + 1,
                result="failed",
                now=now,
            )
            raise _otp_invalid()

        await self._append_attempt(
            tenant_id=tenant_id,
            challenge_id=challenge_id,
            attempt_no=attempt_count + 1,
            result="success",
            now=now,
        )
        await self.session.execute(
            update(otp_challenges)
            .where(
                otp_challenges.c.tenant_id == tenant_id,
                otp_challenges.c.id == challenge_id,
            )
            .values(verified_at=now)
        )

    async def _attempt_count(self, *, tenant_id: UUID, challenge_id: UUID) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(otp_attempts)
                .where(
                    otp_attempts.c.tenant_id == tenant_id,
                    otp_attempts.c.otp_challenge_id == challenge_id,
                )
            )
            or 0
        )

    async def _append_attempt(
        self,
        *,
        tenant_id: UUID,
        challenge_id: UUID,
        attempt_no: int,
        result: str,
        now: datetime,
    ) -> None:
        await self.session.execute(
            insert(otp_attempts).values(
                id=uuid4(),
                tenant_id=tenant_id,
                otp_challenge_id=challenge_id,
                attempt_no=attempt_no,
                result=result,
                created_at=now,
            )
        )


def mask_gsm(gsm: str) -> str:
    digits = "".join(character for character in gsm if character.isdigit())
    if len(digits) <= 4:
        return "****"
    return f"{'*' * max(len(digits) - 4, 0)}{digits[-4:]}"


def _generate_code() -> str:
    return str(secrets.randbelow(10**OTP_DIGITS)).zfill(OTP_DIGITS)


def _hash_code(*, secret_key: str, challenge_id: UUID, code: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        f"{challenge_id}:{code.strip()}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _otp_invalid() -> ApiError:
    return ApiError(
        status_code=422,
        code="otp_invalid",
        message="OTP code is invalid.",
    )
