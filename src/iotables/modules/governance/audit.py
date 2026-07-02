from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from iotables.database.schema import audit_events


@dataclass(frozen=True)
class AuditEvent:
    audit_event_id: UUID
    tenant_id: UUID | None
    actor_user_id: UUID | None
    action: str
    target_type: str
    target_id: str
    reason: str | None
    metadata: dict[str, Any]
    created_at: datetime

    def as_api_payload(self) -> dict[str, Any]:
        return {
            "auditEventId": str(self.audit_event_id),
            "tenantId": str(self.tenant_id) if self.tenant_id else None,
            "actor": {"userId": str(self.actor_user_id)} if self.actor_user_id else None,
            "action": self.action,
            "target": {"type": self.target_type, "id": self.target_id},
            "reason": self.reason,
            "metadata": self.metadata,
            "createdAt": self.created_at.isoformat(),
        }


class AuditQueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def query_platform_audit(
        self,
        *,
        tenant_id: UUID | None,
        action: str | None,
        from_at: datetime | None,
        to_at: datetime | None,
        cursor: int,
        limit: int,
    ) -> tuple[list[AuditEvent], int | None]:
        bounded_limit = min(max(limit, 1), 100)
        bounded_cursor = max(cursor, 0)
        filters = []
        if tenant_id is not None:
            filters.append(audit_events.c.tenant_id == tenant_id)
        if action:
            filters.append(audit_events.c.action == action)
        if from_at is not None:
            filters.append(audit_events.c.created_at >= from_at)
        if to_at is not None:
            filters.append(audit_events.c.created_at <= to_at)

        query: Select[Any] = (
            select(audit_events)
            .order_by(audit_events.c.created_at.desc())
            .offset(bounded_cursor)
            .limit(bounded_limit + 1)
        )
        if filters:
            query = query.where(and_(*filters))

        rows = (await self.session.execute(query)).mappings().all()
        page_rows = rows[:bounded_limit]
        next_cursor = bounded_cursor + bounded_limit if len(rows) > bounded_limit else None
        return (
            [
                AuditEvent(
                    audit_event_id=row["id"],
                    tenant_id=row["tenant_id"],
                    actor_user_id=row["actor_user_id"],
                    action=row["action"],
                    target_type=row["target_type"],
                    target_id=row["target_id"],
                    reason=row["reason"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                )
                for row in page_rows
            ],
            next_cursor,
        )
