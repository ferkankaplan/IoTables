# Database Documentation

This folder turns the semantic app and module model into a PostgreSQL v1 database design.

| Document | Purpose |
| --- | --- |
| [schema.md](schema.md) | Physical table, column, type, ownership, and persistence decisions. |
| [indexes-constraints.md](indexes-constraints.md) | Required unique constraints, foreign keys, check constraints, partial indexes, and query indexes. |
| [migrations.md](migrations.md) | Alembic migration, rollback, data migration, and unsafe-change policy. |
| [seed-provisioning.md](seed-provisioning.md) | Tenant provisioning and one-time starter data strategy. |
| [transactions.md](transactions.md) | Critical transaction boundaries, lock ordering, rollback, idempotency, and concurrency tests. |

The database documents must not invent product behavior. If a table, status, permission, or lifecycle rule conflicts with app or module semantics, update the app/module source first, then update these database documents.
