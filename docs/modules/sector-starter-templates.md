# Module: Sector Starter Templates

## Purpose

Sector Starter Templates owns one-time creation of starter tenant data based on the selected restaurant sector.

It is a provisioning helper, not a runtime seeding mechanism.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Sector enum | Classification | define supported starter sectors |
| Starter template | Template | define starter halls, tables, stations, products, staff, default tenant settings |
| Starter application record | Safety record | record one-time application per tenant |

## Not Owned

- Runtime tenant configuration after creation.
- Tenant lifecycle.
- User authentication beyond requesting bootstrap user creation.
- Menu/product behavior after creation.
- Staff permissions after creation.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp | apply selected starter template during tenant creation | One time per tenant |
| TenantApp | edit resulting starter data | Normal tenant-owned data after creation |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Get sector options | Show sector enum | PlatformApp |
| Apply starter template | Create starter tenant data | PlatformApp provisioning |
| Get starter application state | Prevent reruns | PlatformApp, TenantApp |

## Internal Rules

- Starter data runs only during tenant creation.
- Starter data must never run on server startup, restart, deployment, migration, or release upgrade.
- Changing tenant sector after creation must not re-run starter data.
- Resulting records are normal tenant-owned editable data.
- A durable application record must exist before the operation is considered complete.
- V1 supports only the `cafe` sector starter template.
- Starter template versions use monotonic semantic identifiers such as `cafe.v1`.
- A later template version must not apply automatically to an existing tenant.
- Initial `cafe` starter data enables service delivery tracking by default.

## Operational Safety

- Applying starter template must be idempotent by `tenantId + templateVersion`.
- Partial failure must either rollback all starter records or mark provisioning as failed for manual recovery.
- Re-running after completion is forbidden unless an explicit manual recovery tool exists.
- Starter application should be audited.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| Sector | Enum/config | initial value: `cafe` |
| StarterTemplate | Template definition | versioned |
| StarterTemplateApplication | One-time application record | tenant, template, version, appliedAt |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Select sector and apply starter template |
| TenantApp | Edit created starter data |

## Future Service Boundary

- Own data: template definitions and application records.
- Own APIs: list sectors, apply template, get application state.
- Published events: starter_template.applied.
- Consumed events: tenant.created.
- Must not leak: repeated seed logic into runtime boot.

## Open Questions

None currently.
