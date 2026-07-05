# API Contracts: Tenant Operational Settings

Source contracts: [tenant-operational-settings-contracts.md](tenant-operational-settings-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Tenant Operational Settings exposes tenant-owned customer-visible display settings and service delivery tracking mode.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/tenant-setup/operational-settings` | TenantApp | `tenant_operational_settings.get_settings` | Tenant Admin session | none | `TenantOperationalSettings` | `not_authorized`, `tenant_settings_missing` |
| `PATCH` | `/api/tenant-setup/operational-settings` | TenantApp | `tenant_operational_settings.update_settings` | Tenant Admin session + CSRF | Body: `TenantOperationalSettingsUpdate` | `TenantOperationalSettings` | `validation_failed`, `tenant_settings_missing` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `tenant_operational_settings.get_public_display_context` | Composed into safe tenant context/public page responses. |
| `tenant_operational_settings.is_service_delivery_tracking_enabled` | Used by Service Delivery guards and visibility mapping. |

## Request Schemas

`TenantOperationalSettingsUpdate`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `publicDisplayName` | string/null | no | Optional customer-visible display name. Null/empty falls back to immutable tenant name. |
| `serviceDeliveryTrackingEnabled` | boolean | no | Explicit tenant setting that controls ServiceStaffApp authority. |

## Response Schemas

`TenantOperationalSettings`:

| Field | Type | Notes |
| --- | --- | --- |
| `tenantId` | string | Current tenant. |
| `publicDisplayName` | string/null | Optional public label. |
| `serviceDeliveryTrackingEnabled` | boolean | Controls ServiceStaffApp runtime authority and customer/cashier status semantics. |
| `updatedAt` | timestamp | UTC. |

## Idempotency

Settings updates do not require `Idempotency-Key`. Repeating the same compatible update returns the current settings. Backend validation, tenant scope, and audit protect the operation.
