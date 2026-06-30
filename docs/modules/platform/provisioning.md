# Module: Provisioning

## Purpose

Provisioning owns the tenant creation orchestration that turns a PlatformApp create-tenant command into an active tenant or a recoverable provisioning failure.

It coordinates Platform Tenant Registry, Access, Sector Starter Templates, and Tenant Setup without taking over their owned data.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Provisioning workflow | Workflow | start, complete, fail, retry through explicit recovery |
| Provisioning status | State | provisioning, active, provisioning_failed handoff |
| Provisioning recovery record | Safety record | store safe failure summary and retry metadata |
| Provisioning transaction boundary | Rule | define atomic database work and recovery behavior |

## Not Owned

- Tenant identity fields, owned by Tenant Registry.
- User credentials and roles, owned by Access.
- Starter template definitions and application record, owned by Sector Starter Templates.
- Halls, tables, stations, menu, and display setup records after creation, owned by Tenant Setup.
- DNS record creation, which is manual in v1.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp / Platform Owner | create tenant and inspect provisioning state | Global platform scope |
| PlatformApp / Platform Owner | retry or inspect failed provisioning through explicit recovery tooling | Must not silently rerun completed starter data |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Start tenant provisioning | Create tenant and required initial records | PlatformApp |
| Get provisioning state | Show progress or failure | PlatformApp |
| Retry failed provisioning | Explicit recovery for failed tenant creation | PlatformApp recovery tooling |

## Internal Rules

- Tenant creation starts in `provisioning`.
- Required initial records must commit before the tenant becomes `active`.
- Failed provisioning must end in `provisioning_failed` with a safe error summary.
- One-time starter template application must be durable and must not rerun after completion.
- Tenant name and subdomain immutability begins at creation.
- Manual DNS readiness is tracked after provisioning; DNS is not automated in v1.

## Operational Safety

- Provisioning must be idempotent by tenant identity/subdomain and guarded by database constraints.
- Atomic database work should run in a single transaction where possible.
- External side effects such as OTP/SMS must have explicit retry/recovery behavior.
- Partial failure must not leave an apparently active tenant with missing required setup.
- Recovery tooling must distinguish incomplete provisioning from completed one-time starter application.
- Database-level migration and provisioning rules are defined in [../../database/migrations.md](../../database/migrations.md) and [../../database/seed-provisioning.md](../../database/seed-provisioning.md).

## Data Model

Provisioning coordinates durable state owned by other modules. It does not own tenant setup records after creation.

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Tenant | provisioning -> active / provisioning_failed | owned by Tenant Registry: identity, status, provisioningError | Tenant is activated only after required setup records commit; failed flow must not look active | Preserve failed state for explicit recovery or approved deletion |
| StarterTemplateApplication | pending -> applied / failed / recovery_needed | owned by Sector Starter Templates: tenant, templateKey, templateVersion, status | One-time starter application is the durable seed-rerun guard | Preserve as proof even if starter data is edited later |
| AuditEvent | append-only | owned by Governance: actor/system, action, target, metadata | Critical provisioning state changes must be auditable | Append-only |
| OutboxMessage / MessageDelivery | pending -> completed / failed | owned by Governance or OTP Messaging for non-transactional side effects | External side effects such as SMS must not be assumed to rollback with tenant creation | Preserve attempts according to side-effect retention policy |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Create tenant, inspect provisioning state, run explicit recovery |

## Future Service Boundary

- Own data: provisioning workflow state and recovery metadata.
- Own APIs: start provisioning, inspect provisioning, retry failed provisioning.
- Published events: tenant.provisioning_started, tenant.activated, tenant.provisioning_failed.
- Consumed events: starter_template.applied, user.created.
- Must not leak: tenant runtime mutation into PlatformApp.

## Open Questions

None currently.
