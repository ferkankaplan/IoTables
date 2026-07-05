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
| Tenant lifecycle status | State | provisioning, active, suspended, provisioning_failed |
| Tenant health summary | Read model | expose high-level platform health |

## Not Owned

- Tenant runtime orders.
- Table sessions and payments.
- Staff role assignment details.
- QR token generation.
- Menu/product definitions.
- Tenant creation orchestration, owned by Provisioning.
- DNS record creation and wildcard namespace health, owned by deployment/ops.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp / Platform Owner | create and manage tenants | Global platform scope |
| TenantApp | read current tenant identity and update allowed tenant profile fields | Own tenant only; cannot change name, subdomain, lifecycle, or platform-only health |
| CustomerApp and staff apps | resolve tenant by subdomain | Read-only availability check |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Register tenant identity | Create tenant identity and initial platform metadata | Provisioning |
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
- New tenants start as `provisioning`.
- Tenants become `active` only after required setup records commit successfully.
- `provisioning_failed` tenants require explicit recovery or deletion tooling.
- Suspended tenants must block tenant runtime actions.
- Tenant subdomain route availability depends on the deployment wildcard DNS namespace, not a Tenant Registry field.
- Current release tenant health is limited to lifecycle state, setup/provisioning state, starter template state, tenant admin bootstrap state, and platform-visible runtime error summary when available.
- Platform support actions in the current release are limited to tenant metadata inspection, platform audit inspection, suspend/reactivate, tenant GSM update, and failed-provisioning recovery tooling. PlatformApp does not directly rewrite tenant runtime records.

## Operational Safety

- Tenant identity registration must be idempotent or protected by unique constraints.
- Tenant subdomain uniqueness must be enforced in the database.
- Tenant creation orchestration and rollback/recovery behavior are owned by Provisioning.
- Tenant status changes must be audited.
- Wildcard DNS is outside the app; PlatformApp must not expose tenant-level DNS controls in the current release.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Tenant | provisioning -> active -> suspended/reactivated or provisioning_failed | id, immutable name, immutable subdomain, GSM, sector, capacity, address, status, provisioningError | subdomain unique; name/subdomain immutable; GSM required and audited; sector changes do not re-run starter data; suspended tenants block runtime actions | Do not hard-delete after runtime records exist; failed provisioning needs explicit recovery/deletion tooling |
| TenantHealth | recalculated/read-only | tenant, lifecycle/setup state, starter application state, tenant admin bootstrap state, safe runtime error summary | High-level platform signal only; must not expose tenant runtime detail or mutate tenant data | Derived/read model; can be rebuilt from source state where practical |
| TenantLifecycleEvent | append-only | tenant, previousStatus, nextStatus, actor/system, reason, createdAt | Every suspend/reactivate/provisioning failure should leave a lifecycle event and audit evidence | Append-only; never rewrite status history |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Primary tenant lifecycle surface; create-tenant command enters Provisioning |
| TenantApp | Reads own tenant profile and updates allowed profile fields through Tenant Registry commands |
| CustomerApp/staff apps | Resolve tenant and enforce availability |

## Future Service Boundary

- Own data: tenant identity, tenant lifecycle, tenant platform metadata.
- Own APIs: register tenant identity, resolve tenant, update profile, suspend/reactivate.
- Published events: tenant.created, tenant.updated, tenant.suspended, tenant.reactivated.
- Consumed events: health signals from runtime modules.
- Must not leak: platform-only controls into tenant apps.

## Open Questions

None currently.
