# Runtime Deployment

This document defines the production deployment policy for IoTables. It does not prescribe a final hosting provider or container topology.

Source context:

- [../stack.md](../stack.md)
- [../adr/modular-monolith.md](../adr/modular-monolith.md)
- [../database/migrations.md](../database/migrations.md)
- [../database/seed-provisioning.md](../database/seed-provisioning.md)
- [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)
- [observability.md](observability.md)
- [configuration.md](configuration.md)

External operational references:

- [Cloudflare SSL/TLS encryption modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)
- [Cloudflare Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/)
- [Cloudflare Error 521](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-521/)

## Deployment Shape

IoTables current release is deployed as a modular monolith:

| Runtime Unit | Responsibility |
| --- | --- |
| Frontend build | React/Vite app surfaces for six apps. |
| Backend API | FastAPI app exposing app/module API contracts. |
| PostgreSQL | Shared production database with tenant-owned rows. |
| Background worker | Durable outbox/side-effect processing when implemented. |
| Static assets | Frontend assets served by chosen deployment layer. |

Separate services may be extracted later only if they preserve documented module boundaries.

## GitHub-to-VPS Deployment Path

Production and staging releases are driven by GitHub Actions. Each VPS is a Docker Compose runtime target; operators should not SSH into a VPS for normal releases after the initial host setup is complete.

Branch promotion is linear and must not be bypassed:

```text
feature/* -> integration -> staging -> production
```

`integration` is the non-deploying integration branch and repository default branch. It is the normal merge target for completed feature branches and must pass CI. `staging` is the staging deployment branch and deploys to the staging VPS. `production` is the production deployment branch and deploys to production. Feature branches must not merge directly into `staging` or `production`; hotfixes must be propagated back so all three long-lived branches remain synchronized. Legacy `main` and `master` branch names are not part of the IoTables deployment model after branch migration is complete.

Branch responsibility matrix:

| Branch | Purpose | Normal target | CI | Deploy | GitHub environment | Runtime target | Public namespace |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `feature/<short-kebab-slug>` | New product or technical capability | `integration` | Pull request | No | none | none | none |
| `fix/<short-kebab-slug>` | Non-production bug fix before deployment | `integration` | Pull request | No | none | none | none |
| `docs/<short-kebab-slug>` | Documentation-only change | `integration` | Pull request | No | none | none | none |
| `chore/<short-kebab-slug>` | Tooling, dependency, or repository maintenance | `integration` | Pull request | No | none | none | none |
| `hotfix/<short-kebab-slug>` | Production-impacting fix | `staging`, then `production`, then back to `integration` | Pull request | No direct deploy | none | none | none |
| `integration` | Coherent integration baseline and default branch | `staging` | Push and pull request | No | none | none | none |
| `staging` | Production candidate verification | `production` | Push and pull request | Yes | `staging` | Staging VPS | `tabflow.uk` |
| `production` | Live tenant/customer traffic | release tag after smoke | Push and approved promotion | Yes | `production` | Production VPS | `iotables.net` |

Long-lived branch-to-environment mapping:

| Branch | GitHub environment | Domain namespace | VPS host | Runtime target |
| --- | --- | --- | --- | --- |
| `integration` | none | none | none | CI only; no deploy |
| `staging` | `staging` | `tabflow.uk`, `platform.tabflow.uk`, `*.tabflow.uk` | `185.169.180.201` | Staging VPS |
| `production` | `production` | `iotables.net`, `platform.iotables.net`, `*.iotables.net` | `31.57.187.226` | Production VPS |

Public app surface matrix:

| App surface | Staging URL | Production URL |
| --- | --- | --- |
| PlatformApp | `https://platform.tabflow.uk` | `https://platform.iotables.net` |
| Platform login | `https://platform.tabflow.uk/login` | `https://platform.iotables.net/login` |
| Tenant public page | `https://[tenant].tabflow.uk/` | `https://[tenant].iotables.net/` |
| Tenant login | `https://[tenant].tabflow.uk/login` | `https://[tenant].iotables.net/login` |
| Tenant admin workspace | `https://[tenant].tabflow.uk/admin` | `https://[tenant].iotables.net/admin` |
| CustomerApp | `https://[tenant].tabflow.uk/order` | `https://[tenant].iotables.net/order` |
| StationStaffApp | `https://[tenant].tabflow.uk/station` | `https://[tenant].iotables.net/station` |
| ServiceStaffApp | `https://[tenant].tabflow.uk/service` | `https://[tenant].iotables.net/service` |
| CashierApp | `https://[tenant].tabflow.uk/cashier` | `https://[tenant].iotables.net/cashier` |
| Health check | `https://tabflow.uk/health` | `https://iotables.net/health` |

The staging namespace uses `tabflow.uk` so staging tenant subdomains do not collide with production tenant subdomains under `iotables.net`. Runtime image deploys use immutable `sha-<commit>` tags; moving convenience tags are separated as `production-latest` and `staging-latest`. Convenience tags are not rollback identifiers.

Cloudflare is the public DNS and edge proxy for both namespaces. Public DNS records are proxied, but edge proxying is not a substitute for origin security. IoTables requires Cloudflare SSL/TLS `Full (strict)` mode so browser-to-Cloudflare and Cloudflare-to-origin traffic are both encrypted and the origin certificate is validated. Cloudflare `Flexible` mode is not allowed because it would send Cloudflare-to-origin traffic over plaintext HTTP and would contradict the HTTPS-only deployment contract.

Each VPS must listen on origin HTTPS port `443` through the deployment nginx container. Port `80` exists only to redirect to HTTPS. The public `DEPLOY_HEALTH_URL` values must remain HTTPS URLs.

Staging builds the deployable runtime images. Production does not rebuild the same commit. Production promotion reuses the existing `sha-<commit>` images that already passed staging and moves only the `production-latest` convenience tags. The production environment approval must happen before any production tag is moved or any VPS state is changed. If the `sha-<commit>` images do not exist, production deployment must fail closed.

The `staging -> production` promotion must preserve the exact tested commit SHA. Squash merges, rebase merges, or merge commits that create a new production commit are not acceptable for deployment promotion because they would point production at an artifact that never passed staging. Use a controlled fast-forward promotion, or an equivalent approved branch update that leaves `production` on the same commit that was tested on `staging`.

## Branch and Environment Protection

Long-lived branches must be protected by repository rulesets:

| Branch | Ruleset | Enforced Rules |
| --- | --- | --- |
| `integration` | `protect-integration` | Pull request required, `Lint, test, and build` required, `Build runtime images` required, stale review threads resolved, no deletion, no force-push |
| `staging` | `protect-staging` | Pull request required, `Lint, test, and build` required, `Build runtime images` required, stale review threads resolved, no deletion, no force-push |
| `production` | `protect-production-promotion` | `Lint, test, and build` required, `Build runtime images` required, successful `staging` deployment required, linear history required, no deletion, no force-push |

`production` intentionally does not require a pull request because production must be advanced to the exact commit that already passed staging. Production update authority is constrained by the `protect-production-promotion` ruleset, the deploy workflow's staged-commit check, and the production environment approval gate.

GitHub Environments must also restrict deployments:

| GitHub Environment | Allowed Deployment Branch | Admin Bypass | Required Review |
| --- | --- | --- | --- |
| `staging` | `staging` only | Disabled | Not required |
| `production` | `production` only | Disabled | Required and enforced by GitHub required reviewers |

The required production reviewer is the repository owner account until a broader release-approval group exists.

The workflow itself also fails closed when manually dispatched from any branch other than `staging` or `production`.

Temporary branch names use lowercase kebab-case after a slash:

| Branch Pattern | Naming Rule |
| --- | --- |
| `feature/<short-kebab-slug>` | Lowercase, hyphen-separated, capability-oriented slug |
| `fix/<short-kebab-slug>` | Lowercase, hyphen-separated, defect-oriented slug |
| `hotfix/<short-kebab-slug>` | Lowercase, hyphen-separated, production-impacting slug |
| `docs/<short-kebab-slug>` | Lowercase, hyphen-separated, documentation slug |
| `chore/<short-kebab-slug>` | Lowercase, hyphen-separated, maintenance slug |

Commit messages should follow Conventional Commits format where practical: `type(scope): summary`. Use `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, or `build`; mark breaking changes explicitly with `!` and a body note.

Production releases may be labeled after a successful production smoke check with SemVer tags:

```text
vMAJOR.MINOR.PATCH
```

Use `MAJOR` for incompatible public API/data-contract changes, `MINOR` for backward-compatible capability, and `PATCH` for backward-compatible fixes. Tags are release evidence and changelog anchors; branch promotion remains the deployment trigger in the current workflow.

## Hotfix Flow

Hotfixes do not bypass staging:

```text
hotfix/* -> staging -> production
```

After production deploy, the same fix must be merged or cherry-picked back into `integration`. If the hotfix changes schema, API contracts, auth, payment, ordering, or deployment assumptions, document the migration and rollback path before the hotfix is promoted.

DNS records are managed manually in the current release:

| Environment | DNS records | Target |
| --- | --- | --- |
| Production | `iotables.net`, `platform.iotables.net`, `*.iotables.net` | `31.57.187.226` |
| Staging | `tabflow.uk`, `platform.tabflow.uk`, `*.tabflow.uk` | `185.169.180.201` |

Cloudflare SSL/TLS requirements:

| Environment | Cloudflare SSL/TLS mode | Required origin certificate coverage | Required origin port |
| --- | --- | --- | --- |
| Staging | `Full (strict)` | `tabflow.uk`, `*.tabflow.uk` | `443` |
| Production | `Full (strict)` | `iotables.net`, `*.iotables.net` | `443` |

Each origin certificate may be issued by Cloudflare Origin CA or by a publicly trusted certificate authority, but it must be unexpired and match the requested hostname. The certificate and private key are VPS-owned host configuration, not repository files.

Repository-owned deployment files:

| File | Responsibility |
| --- | --- |
| `.github/workflows/ci.yml` | Runs lint, backend tests, frontend build, and runtime image builds for pull requests, `integration`, `staging`, and `production`. |
| `.github/workflows/deploy.yml` | Verifies only `production` or `staging`, builds staging images, verifies existing SHA images for production, moves production convenience tags only after production environment approval, checks required VPS `.env` and origin TLS files, uploads deploy compose/nginx files, runs migrations, restarts Compose services, and performs a smoke check against the matching GitHub environment. Manual dispatch from any other branch fails closed. |
| `compose.deploy.yaml` | Defines the VPS runtime using immutable `sha-<commit>` image tags, publishes HTTP/HTTPS ports, and mounts VPS-owned nginx config plus origin TLS certificate files. |
| `frontend/Dockerfile.production` | Builds the React/Vite frontend and serves static assets with nginx over the ports supplied by deployment config. |
| `deploy/nginx/default.conf` | Redirects HTTP to HTTPS, terminates origin TLS, routes `/health` and `/api/` to the backend service, and routes all other paths to the SPA. |

The first VPS setup is manual and must install Docker with the Compose plugin, create the `/opt/iotables` release directory, create a deployment user with least-privilege Docker access, write the environment-specific `.env` file, and install the environment-specific origin TLS certificate files in the release directory. After that, a push to the mapped branch performs the release.

The deployment user convention is:

```text
iotables-deploy
```

Staging and production must use separate Ed25519 SSH key pairs. The private key belongs only in the matching GitHub Environment secret. Because GitHub Actions uses the key non-interactively, deployment private keys must not have a passphrase. The public key is installed only on the matching VPS under the `iotables-deploy` user's `authorized_keys`. Do not reuse a human SSH key, root SSH key, or GitHub account key as a deployment key.

Required GitHub Environment secrets:

| Secret | Purpose |
| --- | --- |
| `DEPLOY_HOST` | VPS hostname or IP for the selected GitHub environment. |
| `DEPLOY_USER` | SSH user used by the workflow; current convention is `iotables-deploy`. |
| `DEPLOY_SSH_PRIVATE_KEY` | Private key for the environment-specific deployment user key pair. |
| `DEPLOY_SSH_PORT` | Optional SSH port; defaults to `22`. |
| `DEPLOY_HEALTH_URL` | Public smoke URL for the selected GitHub environment, for example `https://iotables.net/health` or `https://tabflow.uk/health`. |

The VPS release directory must contain `.env` with:

```dotenv
POSTGRES_DB=iotables
POSTGRES_USER=iotables
POSTGRES_PASSWORD=<strong database password>
IOTABLES_ENV=production
IOTABLES_DATABASE_URL=postgresql+asyncpg://iotables:<strong database password>@db:5432/iotables
IOTABLES_SECURITY_SECRET_KEY=<strong application secret>
IOTABLES_CORS_ORIGINS=["https://platform.iotables.net"]
IOTABLES_TENANT_ROOT_DOMAINS=["iotables.net"]
IOTABLES_HTTP_PORT=80
IOTABLES_HTTPS_PORT=443
```

For staging, the same file shape applies on the staging VPS, but `IOTABLES_ENV=staging`, CORS, and tenant root domain values must use `tabflow.uk`, such as `IOTABLES_CORS_ORIGINS=["https://platform.tabflow.uk"]` and `IOTABLES_TENANT_ROOT_DOMAINS=["tabflow.uk"]`.

The VPS `.env` file is host-owned configuration and must not be committed. If public package visibility is disabled for GHCR images, the deployment user also needs registry credentials with permission to pull the repository packages.

The VPS release directory must also contain origin TLS files:

```text
/opt/iotables/certs/origin.pem
/opt/iotables/certs/origin.key
```

Recommended ownership and permissions:

```text
/opt/iotables/certs              iotables-deploy:iotables-deploy 700
/opt/iotables/certs/origin.pem   iotables-deploy:iotables-deploy 644
/opt/iotables/certs/origin.key   iotables-deploy:iotables-deploy 600
```

The deploy workflow fails closed when `.env`, `IOTABLES_HTTP_PORT`, `IOTABLES_HTTPS_PORT`, `certs/origin.pem`, or `certs/origin.key` is missing.

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
- DNS records for tenant subdomains are manual in the current release: `[tenant].tabflow.uk` in staging and `[tenant].iotables.net` in production.
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

The current release does not require a full zero-downtime platform, but releases should prefer:

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
