# ADR: Reliable Side Effects with Outbox Records

## Status

Accepted for the current release.

## Context

Some IoTables operations need external effects that cannot roll back with a database transaction: SMS, printer jobs, fiscal calls, payment-provider calls, DNS automation, notifications, or device communication.

The current architecture places durable side-effect coordination under Governance / Reliable Side Effects.

Sources:

- [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)
- [../modules/governance/reliable-side-effects-contracts.md](../modules/governance/reliable-side-effects-contracts.md)
- [../database/transactions.md](../database/transactions.md)
- [../database/schema.md](../database/schema.md)
- [../database/indexes-constraints.md](../database/indexes-constraints.md)

## Decision

The current release uses durable outbox records and external effect attempt records for non-transactional side effects.

Rules:

- Business state changes commit in the owning module transaction.
- A side effect must not be executed before its source business decision commits.
- When possible, the source transaction inserts an OutboxMessage with a stable idempotency reference.
- Workers claim outbox rows with a bounded lease and record every external attempt.
- Provider responses are redacted before storage.
- Failed and stale side effects must remain visible for recovery.
- Retrying an effect must reuse the original idempotency reference.
- OTP Messaging may keep OTP-specific delivery attempt records, but new external integrations should use Reliable Side Effects by default.

## Consequences

- External effect success is not assumed merely because the business transaction committed.
- Database rollback and Alembic downgrade do not undo external provider calls.
- Features that introduce external effects are not production-ready until retry, recovery, redaction, and idempotency are documented.
- Workers need explicit claim/recover behavior and tests for parallel processing.
- Platform/recovery surfaces may inspect redacted side-effect state but must not mutate business records through this module.

## Synchronization Points

- Reliable Side Effects module: [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)
- Module contracts: [../modules/governance/reliable-side-effects-contracts.md](../modules/governance/reliable-side-effects-contracts.md)
- API contracts: [../modules/governance/reliable-side-effects-api.md](../modules/governance/reliable-side-effects-api.md)
- Transaction catalog: [../database/transactions.md](../database/transactions.md)
- Schema and constraints: [../database/schema.md](../database/schema.md), [../database/indexes-constraints.md](../database/indexes-constraints.md)

## Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Send external requests inside request transaction before commit | It can produce external effects for rolled-back business state. |
| Fire-and-forget after commit without durable record | Worker crashes or process restarts can lose the effect. |
| Provider logs as the only source of truth | They do not preserve local domain context or recovery ownership. |
| Recreate side effects from audit events | Audit explains what happened; it is not a retry queue. |

## Review Trigger

Review this ADR only if a dedicated message broker or workflow engine is introduced. Even then, the durable local source decision and idempotency requirements must remain explicit.
