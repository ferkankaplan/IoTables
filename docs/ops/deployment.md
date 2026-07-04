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

## GitHub-to-VPS Release Path

Production and staging releases are driven by GitHub Actions. Each VPS is a Docker Compose runtime target; operators should not SSH into a VPS for normal releases after the initial host setup is complete.

Branch-to-environment mapping:

| Branch | GitHub environment | Domain namespace | VPS host | Runtime target |
| --- | --- | --- | --- | --- |
| `master` | `production` | `iotables.net`, `*.iotables.net` | `31.57.187.226` | Production VPS |
| `staging` | `staging` | `tabflow.uk`, `*.tabflow.uk` | `185.169.180.201` | Staging VPS |

The staging namespace uses `tabflow.uk` so staging tenant subdomains do not collide with production tenant subdomains under `iotables.net`. Runtime image deploys use commit SHA tags; moving convenience tags are separated as `production-latest` and `staging-latest`.

DNS records are managed manually in v1:

| Environment | DNS records | Target |
| --- | --- | --- |
| Production | `iotables.net`, `*.iotables.net` | `31.57.187.226` |
| Staging | `tabflow.uk`, `*.tabflow.uk` | `185.169.180.201` |

Repository-owned release files:

| File | Responsibility |
| --- | --- |
| `.github/workflows/ci.yml` | Runs lint, backend tests, frontend build, and runtime image builds for pull requests, `master`, and `staging`. |
| `.github/workflows/release.yml` | Verifies `master` or `staging`, publishes backend/frontend images to GHCR, uploads release compose/nginx files, runs migrations, restarts Compose services, and performs a smoke check against the matching GitHub environment. |
| `compose.production.yaml` | Defines the VPS runtime using immutable image tags from the GitHub commit SHA. |
| `frontend/Dockerfile.production` | Builds the React/Vite frontend and serves static assets with nginx. |
| `deploy/nginx/default.conf` | Routes `/api/` to the backend service and all other paths to the SPA. |

The first VPS setup is manual and must install Docker with the Compose plugin, create the `/opt/iotables` release directory, create a deployment user with least-privilege Docker access, and write the environment-specific `.env` file in the release directory. After that, a push to the mapped branch performs the release.

Required GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `VPS_HOST` | VPS hostname or IP. |
| `VPS_USER` | SSH user used by the workflow. |
| `VPS_SSH_PRIVATE_KEY` | Private key for the deployment user. |
| `VPS_SSH_PORT` | Optional SSH port; defaults to `22`. |
| `RELEASE_HEALTH_URL` | Public smoke URL for the selected GitHub environment, for example `https://iotables.net/api/v1/health/live` or `https://tabflow.uk/api/v1/health/live`. |

The VPS release directory must contain `.env` with:

```dotenv
POSTGRES_DB=iotables
POSTGRES_USER=iotables
POSTGRES_PASSWORD=<strong database password>
IOTABLES_DATABASE_URL=postgresql+asyncpg://iotables:<strong database password>@db:5432/iotables
IOTABLES_SECURITY_SECRET_KEY=<strong application secret>
IOTABLES_CORS_ORIGINS=["https://platform.iotables.net"]
IOTABLES_HTTP_PORT=80
```

For staging, the same file shape applies on the staging VPS, but CORS/domain values must use `tabflow.uk`, such as `["https://platform.tabflow.uk"]`.

The VPS `.env` file is host-owned configuration and must not be committed. If public package visibility is disabled for GHCR images, the deployment user also needs registry credentials with permission to pull the repository packages.

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
