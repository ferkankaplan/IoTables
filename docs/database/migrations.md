# Database Migrations and Rollback

This document defines how IoTables changes its PostgreSQL schema and data safely.

It is downstream of [schema.md](schema.md), [indexes-constraints.md](indexes-constraints.md), [../data-model.md](../data-model.md), and the owning module documents. If a migration exposes a semantic gap, update the app/module/domain source before writing the migration.

## Goals

- Keep the database consistent with the six-app semantic model.
- Make schema evolution explicit, reviewed, and reproducible.
- Avoid silent data loss.
- Avoid long locks where practical.
- Treat rollback as an engineered recovery path, not a hopeful `downgrade`.
- Keep business starter data out of schema migrations.

## Tooling

| Area | Decision |
| --- | --- |
| Migration tool | Alembic |
| ORM model source | SQLAlchemy 2 async models |
| PostgreSQL target | PostgreSQL 18.4 |
| Migration topology | Single linear head in the current release |
| Migration execution | Deployment step before application rollout |
| Startup behavior | App startup must not auto-run migrations |

The backend may use async SQLAlchemy at runtime, but Alembic migration scripts should remain boring and deterministic. Migration scripts may use Alembic operations and SQLAlchemy table expressions; they must not import application services that carry runtime side effects.

## Migration File Policy

| Rule | Requirement |
| --- | --- |
| One migration, one purpose | Do not mix unrelated modules or unrelated behavior changes in one revision. |
| Human-reviewed autogenerate | Alembic autogenerate output is a draft, not an accepted migration. |
| Explicit names | Constraint/index names must follow [indexes-constraints.md](indexes-constraints.md#naming). |
| Stable order | Create referenced tables before children; drop children before parents. |
| No hidden seeds | Do not insert tenant starter data, staff users, menu data, or runtime business records from schema migrations. |
| No secret material | Migrations must never embed real passwords, OTP values, session tokens, QR tokens, provider keys, or production data. |
| No broad app imports | Migration files must not import FastAPI routers, service classes, SMS clients, payment clients, or runtime settings with side effects. |

Each migration description should state:

- owning module or cross-module reason;
- affected tables/constraints/indexes;
- whether it is additive, tightening, backfill, destructive, or recovery-only;
- rollback expectation;
- production lock risk if any.

## Migration Categories

| Category | Allowed in Current Release | Rollback Expectation |
| --- | --- | --- |
| Add table | Yes | Drop table is acceptable before data is used; after use, rollback needs approval. |
| Add nullable column | Yes | Drop column is acceptable only before deployed code depends on it. |
| Add non-null column | Yes, with staged backfill | Rollback depends on whether old code still works without it. |
| Add check/unique/FK | Yes, after data validation | Downgrade may drop constraint, but production rollback must consider invalid data risk. |
| Add index | Yes | Drop index is normally safe but may hurt performance. |
| Rename table/column | Avoid unless necessary | Requires compatibility plan; simple downgrade is not enough. |
| Drop table/column | Avoid in the current release | Requires explicit approval, backup, and proof no code/data path uses it. |
| Data backfill | Yes, if bounded and idempotent | Must include compensating or forward-fix plan. |
| Business state migration | Rare | Must be module-owned, audited when meaningful, and never disguised as seed logic. |

## Expand and Contract Pattern

Use expand/contract for changes that affect running code or persisted data.

1. Expand schema with backward-compatible tables/columns/indexes.
2. Deploy code that writes both old and new shape when needed.
3. Backfill existing data in bounded, idempotent steps.
4. Verify data consistency with explicit checks.
5. Tighten constraints after data is valid.
6. Deploy code that reads only the new shape.
7. Contract old schema only after no supported code path depends on it.

Direct rename/drop migrations are not acceptable for user-visible or business-critical records unless the user explicitly approves the break and the recovery plan.

## Transaction Policy

| Migration Work | Transaction Rule |
| --- | --- |
| Normal DDL | Run in Alembic's transactional migration context where PostgreSQL supports it. |
| Small data correction | Run in one transaction if it is bounded and quick. |
| Large backfill | Use batches with restart-safe markers; do not hold one huge transaction. |
| Concurrent index | Use PostgreSQL concurrent index creation with an Alembic autocommit block. |
| Constraint validation | Prefer add-not-valid then validate when lock risk matters. |

Migration scripts must be safe to fail halfway. If a migration cannot be safely retried, it is not ready.

## Rollback Policy

Rollback has three levels:

| Level | Meaning | Use |
| --- | --- | --- |
| Alembic downgrade | Reverse the schema operation for local/dev/test and simple additive changes. |
| Forward fix | Apply a new migration that repairs production state while preserving data. |
| Restore | Restore from backup/snapshot when data loss or corruption cannot be corrected safely. |

Production rollback is not automatically equivalent to `alembic downgrade`.

Rules:

- Every migration must define a `downgrade()` unless it is explicitly marked irreversible.
- Irreversible migrations require a written reason in the migration body and documentation.
- Destructive production changes require a backup/restore decision before deployment.
- Data migrations must define what happens if the application is rolled back while migrated data remains.
- External side effects are never rolled back by database downgrade.
- Do not downgrade across a migration after new production writes have used its schema unless compatibility was designed.

## Data Migration Rules

Data migrations are allowed only when they serve a schema/domain evolution. They are not a substitute for provisioning.

| Rule | Requirement |
| --- | --- |
| Idempotent | Re-running after partial failure must not duplicate records or corrupt state. |
| Scoped | Update by explicit module-owned predicates, not broad fuzzy matches. |
| Bounded | Large updates must batch by stable primary key or timestamp. |
| Auditable when business-visible | If user/business meaning changes, write audit or module history where required. |
| Tenant-safe | Tenant-scoped changes must include `tenant_id` filters and tenant-safe joins. |
| No raw secrets | Never reconstruct or expose credentials, OTPs, tokens, or provider payloads. |

Examples:

| Case | Migration Type |
| --- | --- |
| Add `currency_code` with default `TRY` to price rows | Schema plus deterministic backfill |
| Populate a derived read-model table from source records | Rebuildable backfill |
| Apply new starter menu items to all existing tenants | Not a migration; out of the current release unless explicit product rollout tool exists |
| Retry failed SMS messages | Not a migration; belongs to reliable side-effect recovery |

## One-Time Business Migrations

Some future changes may alter business state, such as introducing a required field to existing menu products. These are not starter seeds.

One-time business migrations must:

- be owned by the affected module;
- be linked to a schema migration or explicit product change;
- record durable completion if re-running would be harmful;
- be idempotent by tenant and target record;
- be testable against partial completion;
- avoid silently changing customer-visible price, order, payment, or session history.

If the operation creates new tenant business records for product convenience, it belongs to a controlled product rollout tool, not Alembic.

## Unsafe Change Rules

Ask for explicit approval before any migration that:

- drops a table or column;
- rewrites historical order, payment, session, audit, or side-effect records;
- changes tenant identity fields;
- weakens a database constraint;
- changes money representation or stored price snapshots;
- changes idempotency key semantics;
- changes login/session/credential/OTP storage;
- changes QR token or table display credential storage;
- requires application downtime.

## Pre-Deployment Checklist

Before merging a migration:

- The owning module document agrees with the schema change.
- [schema.md](schema.md) is updated.
- [indexes-constraints.md](indexes-constraints.md) is updated when constraints/indexes change.
- The Alembic revision has a clear purpose and rollback note.
- Empty-database upgrade to head works.
- Upgrade from the previous head works.
- Downgrade is tested when it is claimed to be safe.
- Data backfills have tests for partial retry.
- Lock risk is documented for large tables or concurrent operations.

## Deployment Order

1. Take backup/snapshot where the migration can affect persisted business data.
2. Stop or drain background workers when they depend on affected tables.
3. Run Alembic migrations.
4. Run post-migration checks.
5. Start the application version compatible with the new schema.
6. Resume workers.
7. Monitor errors, outbox failures, and critical app flows.

For additive migrations designed for zero downtime, application rollout may be split across expand/backfill/contract releases.

## Post-Migration Checks

Minimum checks after migration:

| Area | Check |
| --- | --- |
| Alembic | Database head equals expected revision. |
| Constraints | New unique/check/FK constraints exist with expected names. |
| Tenant isolation | Composite FK assumptions are preserved. |
| Idempotency | Unique indexes for provisioning, order submit, payment record, payment void, cashier correction, and bulk delivery guards exist. |
| Money | Minor-unit money columns contain valid non-floating values. |
| Audit/outbox | Append-only and retry records remain readable. |

## Initial Production Migration Shape

The first implementation migration should create the schema in dependency order:

1. platform and access tables;
2. tenant setup tables;
3. display/presence tables;
4. ordering and settlement tables;
5. fulfillment tables;
6. OTP/messaging tables;
7. governance tables;
8. indexes, constraints, and composite FK guards.

If this first migration becomes too large to review safely, split it by dependency layer while preserving a single linear Alembic head.

## Open Questions

None currently.
