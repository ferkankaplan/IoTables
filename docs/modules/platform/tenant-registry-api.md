# API Contracts: Platform / Tenant Registry

Source contracts: [tenant-registry-contracts.md](tenant-registry-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Tenant Registry owns tenant identity, immutable subdomain/name rules, profile fields, lifecycle status, DNS readiness flag, and platform health summary.

Tenant-scoped apps resolve tenant context from host/subdomain. They must not trust a body/query `tenantId`.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/platform/tenants` | PlatformApp | `tenant_registry.get_health` | Platform Owner session | Query: `status`, `sector`, `q`, `cursor`, `limit` | `TenantHealthList` | `not_authorized` |
| `GET` | `/api/v1/platform/tenants/{tenantId}` | PlatformApp | `tenant_registry.get_profile` | Platform Owner session | Path: `tenantId` | `TenantProfile` | `not_authorized`, `not_found_or_hidden` |
| `PATCH` | `/api/v1/platform/tenants/{tenantId}/profile` | PlatformApp | `tenant_registry.update_profile` | Platform Owner session + CSRF | Body: `gsmNumber?`, `sector?`, `capacity?`, `address?` | `TenantProfile` | `immutable_identity`, `validation_failed` |
| `POST` | `/api/v1/platform/tenants/{tenantId}/status` | PlatformApp | `tenant_registry.change_status` | Platform Owner session + CSRF | Body: `nextStatus`, `reason` | `TenantProfile` | `invalid_lifecycle_transition`, `reason_required` |
| `POST` | `/api/v1/platform/tenants/{tenantId}/dns-ready` | PlatformApp | `tenant_registry.set_dns_ready` | Platform Owner session + CSRF | Body: `dnsReady` | `TenantProfile` | `not_authorized`, `validation_failed` |
| `GET` | `/api/v1/platform/tenants/{tenantId}/lifecycle-events` | PlatformApp | `tenant_registry.get_lifecycle_events` | Platform Owner session | Query: `cursor`, `limit` | `TenantLifecycleEventList` | `not_authorized` |
| `GET` | `/api/v1/tenant/context` | TenantApp, runtime apps | `tenant_registry.resolve_by_subdomain` | Public safe read | Host-derived subdomain | `TenantContext` | `tenant_unavailable` |
| `GET` | `/api/v1/tenant/profile` | TenantApp | `tenant_registry.get_profile` | Tenant Admin session | Host-derived tenant | `TenantProfile` | `not_authorized`, `tenant_unavailable` |
| `PATCH` | `/api/v1/tenant/profile` | TenantApp | `tenant_registry.update_profile` | Tenant Admin session + CSRF | Body: editable profile fields except `name`, `subdomain`, `status`, `dnsReady` | `TenantProfile` | `immutable_identity`, `not_authorized` |

## Request Schemas

`TenantProfileUpdate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `gsmNumber` | string | no | Tenant GSM. Changing it is audited. |
| `sector` | string enum | no | Must be supported by Sector Starter Templates. Does not rerun starter data. |
| `capacity` | integer | no | Optional restaurant capacity. |
| `address` | object/string | no | Optional address shape can be refined before implementation. |

`PATCH` semantics are partial: omitted fields are unchanged, while explicit `null` clears nullable fields. `gsmNumber` cannot be cleared.

`TenantStatusChangeRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `nextStatus` | string enum | yes | Allowed lifecycle target. |
| `reason` | string | yes | Required for suspend/reactivate/recovery-sensitive changes. |

## Response Schemas

`TenantProfile`:

| Field | Type | Notes |
| --- | --- | --- |
| `tenantId` | string | Tenant identifier. |
| `name` | string | Immutable after creation. |
| `subdomain` | string | Immutable after creation. |
| `gsmNumber` | string | Masking may be applied outside edit screens. |
| `sector` | string enum/null | Selected sector. |
| `capacity` | integer/null | Optional. |
| `address` | object/string/null | Optional. |
| `status` | string enum | Tenant lifecycle status. |
| `dnsReady` | boolean | Manual platform checklist flag. |
| `createdAt` | timestamp | UTC. |
| `updatedAt` | timestamp | UTC. |

`TenantHealthList`:

| Field | Type | Notes |
| --- | --- | --- |
| `items` | array of `TenantHealthSummary` | Runtime order/payment details are not exposed. |
| `page` | object | Cursor pagination. |

`TenantHealthSummary` includes `tenantId`, `name`, `subdomain`, `status`, `dnsReady`, `sector`, `provisioningState`, `lastLifecycleEventAt`, safe `healthFlags`, `createdAt`, and `updatedAt`.

`TenantLifecycleEventList`:

| Field | Type | Notes |
| --- | --- | --- |
| `items` | array of `TenantLifecycleEvent` | Most recent lifecycle events first. |
| `page` | object | Cursor pagination. |

`TenantLifecycleEvent` includes `eventId`, `tenantId`, `previousStatus`, `nextStatus`, `actorUserId`, `reason`, and `createdAt`.

`TenantContext` includes `tenantId`, `name`, `subdomain`, `status`, `sector`, and safe public display fields. It must not expose runtime data, platform notes, failure details, or secrets.

## Idempotency

No Tenant Registry endpoint requires `Idempotency-Key` directly. Tenant creation is exposed through [provisioning-api.md](provisioning-api.md), which owns the required tenant creation idempotency behavior.
