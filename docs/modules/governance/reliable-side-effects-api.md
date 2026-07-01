# API Contracts: Reliable Side Effects

Source contracts: [reliable-side-effects-contracts.md](reliable-side-effects-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Reliable Side Effects owns durable outbox messages and redacted external effect attempts for non-transactional side effects such as SMS.

Normal apps do not enqueue or execute side effects directly.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/platform/side-effects/failed` | Platform/recovery tooling | `side_effects.list_failed_effects` | Platform Owner/recovery session | Query: `effectType?`, `status?`, `from?`, `to?`, `cursor`, `limit` | `FailedEffectList` | `not_authorized` |
| `GET` | `/api/v1/platform/side-effects/{outboxMessageId}` | Platform/recovery tooling | `side_effects.get_effect_state` | Platform Owner/recovery session | Path: `outboxMessageId` | `EffectState` | `not_authorized`, `not_found_or_hidden` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `side_effects.enqueue_effect` | Called by business modules after validated decisions, usually in the same DB transaction. |
| `side_effects.claim_next_effect` | Worker-internal direct module call, not public HTTP. |
| `side_effects.record_attempt` | Worker-internal direct module call. |
| `side_effects.mark_completed` | Worker-internal direct module call. |
| `side_effects.mark_failed` | Worker-internal direct module call. |
| `side_effects.recover_stale_claims` | Worker/recovery-internal direct module call. |

## Response Schemas

`EffectState`:

| Field | Type | Notes |
| --- | --- | --- |
| `outboxMessageId` | string | Outbox record. |
| `effectType` | string | Allowed effect type. |
| `aggregateType` | string | Source aggregate type. |
| `aggregateId` | string | Source aggregate ID. |
| `status` | string enum | `pending`, `claimed`, `completed`, `failed`. |
| `attemptCount` | integer | Number of attempts. |
| `nextAttemptAt` | timestamp/null | Retry schedule. |
| `claimExpiresAt` | timestamp/null | Worker lease expiry when status is `claimed`; null otherwise. |
| `lastFailureSummary` | string/null | Redacted. |
| `createdAt` | timestamp | UTC. |
| `updatedAt` | timestamp | UTC. |

`FailedEffectList` uses cursor pagination and includes redacted `EffectState` rows.

## Redaction Rules

Side-effect API responses must not expose provider raw payloads, SMS content beyond safe templates, OTP codes, target full secrets, credentials, or stack traces.

## Idempotency

Outbox enqueue idempotency is owned by the source business decision and `effectType + idempotencyRef` uniqueness. Recovery read endpoints do not require `Idempotency-Key`.
