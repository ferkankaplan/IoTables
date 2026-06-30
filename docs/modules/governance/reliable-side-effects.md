# Module: Reliable Side Effects

## Purpose

Reliable Side Effects owns durable outbox records and external effect attempt records for operations that cannot be rolled back by a database transaction.

It protects the system from losing, duplicating, or silently misreporting side effects such as SMS delivery, printer jobs, fiscal calls, payment-provider calls, DNS automation, notifications, and device communication.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Outbox message | Durable record | create, claim, retry, complete, fail |
| External effect attempt | Attempt log | record provider call attempts and results |
| Retry policy | Execution rule | decide retryability and backoff |
| Idempotency reference | Safety value | preserve provider/client duplicate protection |

## Not Owned

- Business state owned by Platform, Access, Tenant Setup, Ordering, Fulfillment, or Settlement.
- Provider-specific client implementation details.
- Secrets, raw OTP values, payment card data, fiscal private keys, or raw device credentials.
- Domain authorization decisions.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| Domain modules | enqueue side effects after committed business decisions | Must include target, type, payload reference, and idempotency reference |
| Background worker | claim and execute pending effects | Must record every attempt |
| PlatformApp / support workflow | inspect failed side effects when an explicit recovery surface exists | Must not mutate business records through this module |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Enqueue effect | Record a side effect to execute after commit | Domain modules |
| Claim next effect | Let a worker safely reserve work | Background worker |
| Record attempt | Persist provider response, failure, or timeout | Background worker |
| Mark completed | Finish exactly-once logical effect processing | Background worker |
| Mark failed | Stop retrying after policy exhaustion or non-retryable error | Background worker |

## Internal Rules

- A database transaction may enqueue an outbox message with the domain state change it depends on.
- A side effect must not be executed before the domain transaction commits.
- Each outbox message must have a stable idempotency reference scoped to the provider/effect type when the provider supports idempotency.
- Retrying an effect must not create duplicate business records.
- Provider responses must be stored without secrets or sensitive payloads.
- A module may keep an equivalent durable attempt log only when that log provides the same replay, retry, and auditability guarantees. OTP Messaging is allowed to own OTP-specific delivery attempts, but new external integrations should use this module by default.
- In-process domain events are allowed only for pure in-database v1 flows that do not call external systems.

## Operational Safety

- Claiming work must be concurrency-safe.
- Attempts must be append-only or otherwise preserve enough history for recovery.
- Permanent failure must be visible through an explicit support/recovery workflow before the related feature is considered production-ready.
- Retried side effects must include the original outbox idempotency reference.
- Manual replay must require explicit authorization and audit.
- Outbox cleanup must not delete unresolved, failed, or recently completed records without a retention rule.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| OutboxMessage | Side effect to execute | tenant nullable, type, aggregate reference, payload reference, idempotency reference, status |
| ExternalEffectAttempt | Provider execution attempt | outbox message, attempt number, started/completed timestamps, result summary |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Future support/recovery inspection only |

## Future Service Boundary

- Own data: outbox messages and external effect attempts.
- Own APIs: enqueue, claim, record attempt, complete, fail, inspect.
- Published events: side_effect.completed, side_effect.failed if needed.
- Consumed events: committed domain commands that require external side effects.
- Must not leak: external provider secrets or business-state mutation authority.

## Open Questions

None currently.
