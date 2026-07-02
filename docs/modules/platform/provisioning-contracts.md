# Module Contracts: Provisioning

Source module: [provisioning.md](provisioning.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `provisioning.start_tenant` | PlatformApp | tenant name, subdomain, tenant GSM, optional sector/capacity/address, `Idempotency-Key` | Platform Owner only; required tenant identity fields; selected sector must be supported | Reserve `tenant_provisioning_idempotency`; phased flow from [../../database/seed-provisioning.md](../../database/seed-provisioning.md); subdomain and starter application uniqueness prevent duplicate creation | Provisioning result: active tenant or failed state |
| `provisioning.retry_failed` | PlatformApp | tenantId, optional recovery note | Platform Owner only; tenant must be `provisioning_failed` or incomplete `provisioning`; completed starter data must not rerun | Lock tenant and starter application rows; retry only incomplete phase | Updated provisioning state |
| `provisioning.mark_recovery_needed` | Provisioning recovery tooling | tenantId, reason | Platform Owner/recovery workflow only | Lock tenant; preserve failure history | `recovery_needed` starter/provisioning state |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `provisioning.get_state` | PlatformApp | tenantId | Platform Owner only | Tenant lifecycle, starter application state, safe failure summary, DNS checklist |
| `provisioning.get_recovery_summary` | PlatformApp | tenantId | Platform Owner only; no runtime mutation | Missing required setup records and side-effect status |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `tenant_registry.register_identity` | Reserve tenant identity and subdomain. |
| `identity_access.create_bootstrap_user` | Create tenant admin and starter staff users. |
| `staff_access.upsert_staff_profile` | Create staff profiles, roles, and assignments. |
| `sector_starter_templates.apply_template` | Create one-time starter tenant setup records. |
| `audit.record_event` | Record provisioning decisions. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `tenant.provisioning_started` | Tenant creation attempt is reserved | Audit, Platform health |
| `tenant.activated` | Required records commit and tenant becomes active | Platform health |
| `tenant.provisioning_failed` | Required setup fails | Platform health, recovery tooling |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_subdomain` | Tenant identity reservation failed. |
| `idempotency_conflict` | Same Platform Owner reused an idempotency key with a different normalized create-tenant request. |
| `request_processing` | Same Platform Owner repeated a create-tenant request while the original request is still processing. |
| `starter_already_applied` | Retry attempted to rerun completed starter data. |
| `provisioning_incomplete` | Required records did not commit and tenant cannot become active. |
| `recovery_required` | Safe retry cannot be proven without manual recovery. |
