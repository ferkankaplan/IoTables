# Runtime Deployment

This document defines the v1 deployment policy for IoTables. It does not prescribe a final hosting provider or container topology.

Source context:

- [../stack.md](../stack.md)
- [../adr/modular-monolith.md](../adr/modular-monolith.md)
- [../database/migrations.md](../database/migrations.md)
- [../database/seed-provisioning.md](../database/seed-provisioning.md)
- [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)
- [observability.md](observability.md)
- [configuration.md](configuration.md)

## Deployment Shape

IoTables v1 is deployed as a modular monolith:

| Runtime Unit | Responsibility |
| --- | --- |
| Frontend build | React/Vite app surfaces for six apps. |
| Backend API | FastAPI app exposing app/module API contracts. |
| PostgreSQL | Shared v1 database with tenant-owned rows. |
| Background worker | Durable outbox/side-effect processing when implemented. |
| Static assets | Frontend assets served by chosen deployment layer. |

Separate services may be extracted later only if they preserve documented module boundaries.

## Pre-Deploy Checks

Before deployment:

- tests relevant to changed docs/code pass;
- semantic index is regenerated when indexed docs changed;
- environment configuration validates;
- secrets are present in the target environment and not committed;
- Alembic migration plan is reviewed;
- rollback notes exist for migrations;
- provider fake modes are disabled outside local/test;
- one-time starter/provisioning flows are not wired to startup.

## Deployment Order

Use this order unless a specific release note proves another order is safer:

1. Build frontend assets.
2. Build/package backend runtime.
3. Apply reviewed Alembic migrations.
4. Verify database head.
5. Start or restart backend API.
6. Start or restart background workers.
7. Serve new frontend assets.
8. Run readiness checks.
9. Run smoke checks for login, tenant route resolution, database access, and health endpoints.
10. Monitor logs, metrics, outbox, and API errors.

Database migrations should complete before code paths depend on new schema. Destructive migrations require explicit backup/restore and rollout planning from [../database/migrations.md](../database/migrations.md).

## Tenant Provisioning and DNS

- PlatformApp creates tenant records and starter data through the provisioning workflow.
- DNS records for `[tenant].iotables.net` are manual in v1.
- Platform DNS readiness is an explicit PlatformApp state, not an automated DNS provider result.
- Provisioning and starter templates must be idempotent and durable per tenant.
- Starter templates must never rerun on server restart, deployment, migration, or release upgrade.

## Health and Smoke Checks

Minimum post-deploy checks:

| Check | Expected Result |
| --- | --- |
| App readiness | Backend confirms config, DB, and migration head. |
| Platform login route | Login surface loads, no secrets exposed. |
| Tenant public route | Tenant host resolves safe public context. |
| Auth session check | Protected route rejects unauthenticated requests safely. |
| Database query | Basic DB read succeeds. |
| Outbox worker | Worker can read queue or reports disabled intentionally. |
| Semantic docs | `docs/semantic/index.jsonl` exists for documentation workflow. |

Smoke checks must not create demo tenant runtime orders/payments unless the release explicitly tests a disposable environment.

## Rollback

Rollback depends on what changed:

| Change Type | Rollback Rule |
| --- | --- |
| Frontend-only | Re-serve previous assets if API contract remains compatible. |
| Backend additive | Roll back backend if database remains compatible. |
| Database additive | Use Alembic downgrade only when safe; otherwise keep schema and roll code forward/back compatibly. |
| Destructive database | Requires backup/restore decision before deployment. |
| Provider side effect | Use compensating/reconciliation workflow; do not assume transaction rollback. |
| Provisioning failure | Use explicit provisioning recovery state and retry tools. |

Do not use audit events, analytics records, or logs as rollback mechanisms. They are evidence/telemetry, not business-state repair tools.

## Zero-Downtime Direction

V1 does not require a full zero-downtime platform, but releases should prefer:

- additive schema changes before code that uses them;
- backwards-compatible API changes when possible;
- explicit feature gates only when backend guards remain authoritative;
- small migrations with clear lock impact;
- outbox retry safety for external side effects.

Breaking public API, database, auth, payment, or ordering behavior requires explicit review before release.

## Acceptance

Runtime deployment is acceptable when:

- deployment order protects database and module invariants;
- migrations and rollback rules are explicit;
- starter/provisioning flows cannot rerun from deployment;
- health/smoke checks prove readiness without leaking secrets;
- failures are observable through logs, metrics, audit where appropriate, and outbox state.
