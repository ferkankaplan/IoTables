# Module Contracts: Tenant Operational Settings

Source module: [tenant-operational-settings.md](tenant-operational-settings.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `tenant_operational_settings.update_settings` | TenantApp, Provisioning | tenantId, publicDisplayName?, serviceDeliveryTrackingEnabled? | Tenant Admin own tenant or Provisioning; public display name length/format; explicit boolean for tracking changes | Update one settings row; audit TenantApp changes | Updated settings |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `tenant_operational_settings.get_settings` | TenantApp | tenantId | Tenant Admin own tenant | Full tenant operational settings |
| `tenant_operational_settings.get_public_display_context` | TenantApp public page, Tenant Registry composition | tenantId | Public-safe tenant route | Public display name fallback context |
| `tenant_operational_settings.is_service_delivery_tracking_enabled` | Fulfillment, ServiceStaffApp guards, Customer/Cashier visibility mapping | tenantId | Internal or authenticated tenant-scoped caller | Boolean tracking mode |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `tenant_settings.changed` | Public display name or operational setting changes | Audit, public context readers |
| `service_tracking.changed` | Service delivery tracking enabled/disabled | ServiceStaffApp, Fulfillment, Customer/Cashier visibility mapping, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `tenant_settings_missing` | Required settings row does not exist for tenant. |
| `validation_failed` | Public display name or setting payload is invalid. |
| `service_tracking_transition_blocked` | A future rule blocks a tracking-mode change; none currently locked for v1. |
