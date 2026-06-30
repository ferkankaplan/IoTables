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
| Provisioning | apply selected starter template during tenant creation | One time per tenant |
| TenantApp | edit resulting starter data | Normal tenant-owned data after creation |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Get sector options | Show sector enum | PlatformApp |
| Apply starter template | Create starter tenant data | Provisioning |
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

- Applying starter template must be idempotent by `tenantId + templateKey + templateVersion`.
- Partial failure must either rollback all starter records or mark provisioning as failed for manual recovery.
- Re-running after completion is forbidden unless an explicit manual recovery tool exists.
- Starter application should be audited.
- Starter templates must not run from migrations, server startup, restart, deployment, or release upgrade; database rules live in [../../database/seed-provisioning.md](../../database/seed-provisioning.md).

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Sector | configured -> selectable | code, displayName, enabled | `cafe` is the initial v1 sector; disabled sectors cannot be selected for new tenant creation | Preserve historical sector codes used by existing tenants/templates |
| StarterTemplate | drafted/configured -> active -> retired | sector, templateVersion, halls, tables, stations, products, variants, staff, serviceDeliveryTracking default | Template versions are immutable after activation; applying a template must create normal tenant-owned records | Retire instead of mutating active templates used in historical provisioning |
| StarterTemplateApplication | pending -> applied / failed / recovery_needed | tenant, sector, templateKey, templateVersion, status, appliedAt, failureSummary | Unique by tenant + templateKey + templateVersion; successful application must never re-run on restart/deploy/migration/release | Preserve forever as seed-rerun proof |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Select sector as part of tenant creation |
| TenantApp | Edit created starter data |

## Future Service Boundary

- Own data: template definitions and application records.
- Own APIs: list sectors, apply template, get application state.
- Published events: starter_template.applied.
- Consumed events: tenant.created.
- Must not leak: repeated seed logic into runtime boot.

## Open Questions

None currently.
