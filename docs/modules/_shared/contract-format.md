# Module Command/Query Contract Format

Module contracts define what a module exposes to apps and other modules before HTTP/API request-response shapes are designed.

They are not endpoint documents. API contracts must wrap these module contracts without changing ownership, guards, transaction rules, or returned domain meaning.

## Rules

- Commands mutate state or request a side effect.
- Queries read state and must not mutate business records.
- Guards are enforced server-side even if the frontend hides the action.
- Idempotency and transaction boundaries are part of the contract.
- Returned values are domain results, not UI view models.
- A contract may call another module only through that module's public contract.
- If a needed behavior is missing from app scenarios, update the app document first.

## Command Table

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `example.command` | App or module | Required input | Actor/scope/domain checks | Locking, idempotency, rollback | Domain result/events |

## Query Table

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `example.query` | App or module | Tenant/filter/scope | Read permission/freshness | Domain read model |

## Event Table

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `example.event` | Business decision committed | Interested modules/workers |

## Failure Outcomes

Use domain-level failure names here. HTTP status codes belong to API contracts.

| Failure | Meaning |
| --- | --- |
| `not_authorized` | Actor lacks required app/module permission. |
| `wrong_scope` | Actor is valid but not for this tenant/station/hall/table. |
| `invalid_state` | Target exists but current lifecycle does not allow the command. |
| `duplicate_request` | Idempotency guard found an existing compatible result. |
| `conflicting_request` | Same idempotency key or natural key was used for a different request. |
| `not_found_or_hidden` | Target is absent or intentionally hidden from this actor. |
