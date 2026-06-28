# Module: Platform / Tenant Registry

## Purpose

Platform / Tenant Registry owns tenant identity, lifecycle, subdomain, platform-owned tenant metadata, and tenant availability.

It is the source of truth for whether a tenant exists, where it is served, and whether tenant apps may operate.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Tenant | Entity | create, read, update allowed profile fields |
| Tenant name | Immutable identity | create only |
| Tenant subdomain | Immutable identity | create only |
| Tenant GSM number | Sensitive contact | create, update, audit |
| Tenant sector | Classification | create, update without re-provisioning |
| Tenant lifecycle status | State | draft, active, suspended, closed if introduced |
| Tenant health summary | Read model | expose high-level platform health |

## Not Owned

- Tenant runtime orders.
- Table sessions and payments.
- Staff role assignment details.
- QR token generation.
- Menu/product definitions.
- DNS record creation, which is manual in v1.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp / Platform Owner | create and manage tenants | Global platform scope |
| TenantApp | read current tenant identity and editable tenant profile | Own tenant only |
| CustomerApp and staff apps | resolve tenant by subdomain | Read-only availability check |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Create tenant | Register tenant identity and initial metadata | PlatformApp |
| Resolve tenant by subdomain | Route tenant apps safely | All tenant apps |
| Update tenant profile | Edit allowed tenant metadata | PlatformApp, TenantApp |
| Change tenant status | Suspend/reactivate tenant | PlatformApp |
| Get tenant health | Show platform health summary | PlatformApp |

## Internal Rules

- Tenant name is immutable after creation.
- Tenant subdomain is immutable after creation.
- Tenant GSM number is required and editable, but every change must be audited.
- Tenant subdomain must be unique.
- Tenant sector can change after creation but must not re-run starter data.
- Suspended tenants must block tenant runtime actions.

## Operational Safety

- Tenant creation must be idempotent or protected by unique constraints.
- Tenant subdomain uniqueness must be enforced in the database.
- Tenant creation and initial provisioning must have explicit rollback/recovery behavior.
- Tenant status changes must be audited.
- Manual DNS is outside the app; PlatformApp must not claim DNS automation in v1.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| Tenant | Platform tenant record | immutable name/subdomain, GSM, status, sector |
| TenantHealth | Health/read model | derived from runtime signals |
| TenantLifecycleEvent | Lifecycle history | status changes and reasons |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Primary tenant creation and lifecycle surface |
| TenantApp | Reads own tenant profile and edits allowed fields |
| CustomerApp/staff apps | Resolve tenant and enforce availability |

## Future Service Boundary

- Own data: tenant identity, tenant lifecycle, tenant platform metadata.
- Own APIs: create tenant, resolve tenant, update profile, suspend/reactivate.
- Published events: tenant.created, tenant.updated, tenant.suspended, tenant.reactivated.
- Consumed events: health signals from runtime modules.
- Must not leak: platform-only controls into tenant apps.

## Open Questions

- Exact v1 tenant status model: `draft`, `active`, `suspended`, others.
- Exact tenant health signals.
