# Module: Tenant Operational Settings

## Purpose

Tenant Operational Settings owns tenant-owned settings that affect customer-visible identity and runtime fulfillment mode but are not platform identity fields.

It is the source for `public_display_name` and `service_delivery_tracking_enabled`.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Public display name | Configuration | create/update/clear |
| Service delivery tracking mode | Configuration | enable/disable |
| Tenant operational settings row | Entity | one settings row per tenant |

## Not Owned

- Immutable tenant name, subdomain, lifecycle status, DNS readiness, GSM, address, capacity, and sector classification, owned by Platform / Tenant Registry.
- Staff roles and scopes, owned by Access / Staff Access.
- Service delivery queue execution, owned by Fulfillment / Service Delivery.
- Customer orders, table sessions, payments, and cashier corrections.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | read and update settings | Own tenant |
| TenantApp public page | read safe public display fields | Public-safe fields only |
| ServiceStaffApp | read service tracking mode through guards | Read-only |
| Fulfillment / Service Delivery | read service tracking mode | Internal read-only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Get tenant operational settings | Render Tenant Settings | TenantApp |
| Update tenant operational settings | Change public display name or service tracking mode | TenantApp |
| Get public display context | Resolve customer/public display label | TenantApp public page, Tenant Registry composition |
| Read service tracking mode | Guard ServiceStaffApp behavior | Fulfillment |

## Internal Rules

- A tenant has exactly one operational settings row.
- Public display name is optional; public surfaces fall back to immutable tenant name when it is absent.
- Service delivery tracking is explicit tenant configuration.
- When service delivery tracking is disabled, ServiceStaffApp mutation controls are hidden/blocked and `PreparationItem.ready` becomes the final tracked fulfillment state for customer/cashier visibility.
- Re-enabling service delivery tracking affects new ready items going forward; historical disabled-mode items are not retroactively delivered.
- Changing service delivery tracking must not mutate existing DeliveryState records.

## Operational Safety

- Tenant Admin can update only the current tenant's settings.
- Service delivery tracking changes must be audited because they affect staff authority and customer-visible status semantics.
- Runtime Fulfillment commands must re-read the current mode server-side; UI hiding is not enough.
- Settings updates must not expose platform-only tenant identity fields.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| TenantOperationalSettings | created during provisioning -> updated | tenant, publicDisplayName, serviceDeliveryTrackingEnabled | one row per tenant; tenant FK required | Preserve; do not delete while tenant exists |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Tenant Settings workspace, Public Tenant Page |
| ServiceStaffApp | Reads whether delivery tracking is enabled |
| CustomerApp | Receives customer-visible status semantics indirectly |
| CashierApp | Receives fulfillment status semantics indirectly |

## Future Service Boundary

- Own data: tenant operational settings.
- Own APIs: tenant settings read/update.
- Published events: tenant_settings.changed, service_tracking.changed.
- Consumed events: tenant.created/provisioned.
- Must not leak: platform lifecycle controls, tenant runtime records, staff credentials.

## Open Questions

None currently.
