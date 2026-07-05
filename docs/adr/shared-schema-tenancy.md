# ADR: Shared PostgreSQL Schema Tenancy

## Status

Accepted for the current release.

## Context

IoTables serves multiple restaurant tenants. The current production database design uses PostgreSQL `public` schema with shared tables and `tenant_id` on tenant-owned records. Module boundaries are enforced through code ownership, migrations, constraints, and tests rather than separate PostgreSQL schemas.

Sources:

- [../database/schema.md](../database/schema.md)
- [../database/indexes-constraints.md](../database/indexes-constraints.md)
- [../database/migrations.md](../database/migrations.md)
- [../data-model.md](../data-model.md)

## Decision

The current release uses shared PostgreSQL tables with row-level tenant ownership.

Rules:

- Tenant-owned records carry `tenant_id`.
- Platform-global records may use `tenant_id = null` only where explicitly documented, such as Platform Owner identity.
- Tenant isolation is enforced by service guards, composite foreign keys, unique constraints, query filters, and tests.
- PostgreSQL schemas per tenant or per module are out of the current release.
- Tenant hard-delete is out of the current release until retention and legal rules exist.
- Migrations must be tenant-safe and must not create business seed data.

## Consequences

- Every tenant-scoped query must resolve tenant context from trusted routing or authenticated session state.
- Cross-tenant references must be prevented with composite foreign keys where single-column UUID FKs are insufficient.
- Indexes must include leading `tenant_id` where tenant-scoped access is expected.
- Tests must cover tenant isolation at service and database boundaries.
- Module ownership remains semantic and code-level; it is not represented by PostgreSQL schemas in the current release.

## Synchronization Points

- Physical schema: [../database/schema.md](../database/schema.md)
- Constraints and composite FKs: [../database/indexes-constraints.md](../database/indexes-constraints.md)
- Migration rules: [../database/migrations.md](../database/migrations.md)
- Module ownership: [../modules/module-map.md](../modules/module-map.md)
- Data model: [../data-model.md](../data-model.md)

## Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Separate database per tenant | Operationally heavier than current release needs and complicates provisioning/recovery. |
| Separate PostgreSQL schema per tenant | Adds migration and runtime routing complexity before tenant scale proves it necessary. |
| Separate PostgreSQL schema per module | Gives a false sense of boundary while increasing migration complexity. |
| Tenant isolation only in frontend/backend code | Database constraints must help prevent wrong-tenant references. |

## Review Trigger

Review this ADR when tenant scale, compliance, retention, backup/restore, noisy-neighbor isolation, or per-tenant operational lifecycle requires stronger physical isolation than shared tables.
