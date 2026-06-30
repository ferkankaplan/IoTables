# Module Contracts: Reliable Side Effects

Source module: [reliable-side-effects.md](reliable-side-effects.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `side_effects.enqueue_effect` | Modules after business decision | effectType, aggregate ref, payloadRef, idempotencyRef | Source business decision already validated; payload redacted; effect type allowed | Insert OutboxMessage in same DB transaction as source decision when possible; unique effect/idempotency prevents duplicate | Pending outbox message |
| `side_effects.claim_next_effect` | Worker | effect type filters | Worker only | Row-level claim with `select for update skip locked` or equivalent | Claimed message |
| `side_effects.record_attempt` | Worker | outboxMessageId, attemptNo, result summary | Claimed message; redacted provider response | Append ExternalEffectAttempt | Attempt record |
| `side_effects.mark_completed` | Worker | outboxMessageId | Claimed message and successful attempt | Mark completed once; idempotent if already completed | Completed outbox message |
| `side_effects.mark_failed` | Worker | outboxMessageId, retry/permanent result | Claimed message; retry policy applied | Update status and nextAttemptAt or terminal failed state | Failed/retry state |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `side_effects.get_effect_state` | Source module, recovery tooling | aggregate ref or outboxMessageId | Module/recovery scope | Message status and redacted attempts |
| `side_effects.list_failed_effects` | Platform/recovery tooling | filters | Platform/recovery scope | Failed/pending side effects |

## Events

Reliable Side Effects does not publish domain business events. It records and executes external side-effect work requested by other modules.

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_effect` | Same effectType/idempotencyRef already exists. |
| `payload_not_safe` | Payload contains raw secrets or unredacted provider data. |
| `claim_conflict` | Another worker claimed the message. |
| `permanent_failure` | Provider result should not be retried automatically. |
