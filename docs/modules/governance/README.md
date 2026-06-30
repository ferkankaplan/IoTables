# Governance Context

Governance owns audit, policy evidence, and reliable external side-effect records for critical platform, access, tenant setup, ordering, fulfillment, and settlement actions.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [audit.md](audit.md) | Append-only critical action records |
| [reliable-side-effects.md](reliable-side-effects.md) | Durable outbox and attempt records for non-transactional side effects |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [audit-contracts.md](audit-contracts.md) | Audit record and audit query contracts |
| [reliable-side-effects-contracts.md](reliable-side-effects-contracts.md) | Outbox enqueue, worker claim, attempt, retry, and failure contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [audit-api.md](audit-api.md) | Platform, tenant, and operational audit query endpoints |
| [reliable-side-effects-api.md](reliable-side-effects-api.md) | Recovery-visible failed side-effect and effect state endpoints |

## Primary Apps

- PlatformApp
- TenantApp
- CashierApp
- StationStaffApp
- ServiceStaffApp

## Boundary Rule

Governance records evidence and external side-effect execution state. It must not become a backdoor for mutating business state owned by other contexts.
