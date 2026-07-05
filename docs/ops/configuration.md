# Runtime Configuration

This document defines production configuration rules for IoTables runtime services. It is a policy source for implementation, not a committed secret file.

Source context:

- [../stack.md](../stack.md)
- [../api/auth.md](../api/auth.md)
- [../security/threat-model.md](../security/threat-model.md)
- [../security/rate-limits.md](../security/rate-limits.md)
- [../database/migrations.md](../database/migrations.md)
- [../database/seed-provisioning.md](../database/seed-provisioning.md)
- [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)

## Principles

- Configuration is environment-owned, not hard-coded.
- Secrets are never committed.
- Backend settings should be validated at startup through Pydantic Settings.
- Frontend public configuration must contain only non-secret values.
- Missing or unsafe production configuration must fail fast.
- Starter data and seed/provisioning behavior must not run from process startup.

## Environment Classes

| Environment | Purpose | Rules |
| --- | --- | --- |
| local | Developer machine. | Uses the Docker Compose `db` PostgreSQL service by default and local `.env`, ignored by git. |
| test | Automated tests. | Isolated database/schema, deterministic fake providers. |
| staging | Production-like verification. | Realistic secrets/providers, no production data unless explicitly approved. |
| production | Live tenant/customer traffic. | Strict secrets, HTTPS, secure cookies, migrations reviewed. |

## Backend Configuration Groups

| Group | Required Values |
| --- | --- |
| App | environment name, service name, public base URLs, log level. |
| Database | async runtime database URL, migration database URL if separate, pool size/timeouts. |
| Security | session secret, CSRF secret, cookie domain, secure cookie flag, allowed hosts. |
| Platform | platform host, tenant root domain, tenant subdomain policy. |
| Auth | password policy, session TTL, setup-token TTL, TOTP issuer. |
| OTP/SMS | provider mode, sender config, send limits, challenge TTL, fake provider switch for local/test only. |
| QR/Table Presence | token TTL, redemption freshness window, display credential policy. |
| Idempotency | replay retention windows for orders/payments/corrections/bulk delivery. |
| Outbox | worker enabled, batch size, retry schedule, max attempts. |
| CORS/CSRF | allowed origins, protected methods, same-site policy. |
| Observability | log format, metrics enabled, tracing endpoint if used. |

Production must not start with placeholder secrets, local fake providers, insecure cookies, or wildcard host/origin settings.

## Frontend Configuration

Frontend configuration may expose only public values:

| Value | Allowed |
| --- | --- |
| Public app base path | Yes. |
| API base URL for same host | Yes, if non-secret. |
| Platform/tenant host hints | Yes. |
| Build mode | Yes. |
| Feature visibility flags | Yes, only when backend still enforces authority. |
| Secrets, tokens, provider keys | Never. |

Frontend feature flags must not bypass backend module guards, authorization, idempotency, or database invariants.

Local Vite development proxies `/api` to `http://127.0.0.1:8000` so the browser can call the FastAPI service with same-origin paths during development. Production routing must provide the same `/api` path through deployment infrastructure instead of exposing secrets in frontend config.

## Secret Handling

Secrets include:

- database credentials;
- `IOTABLES_SECURITY_SECRET_KEY`, used for encrypting Platform Owner TOTP secret material and other local security primitives until a deployment secret store/KMS is introduced;
- session/CSRF signing keys;
- TOTP encryption keys;
- OTP/SMS provider credentials;
- payment provider credentials if added later;
- raw QR/display credential material;
- external service tokens.

Rules:

- secrets must come from environment variables or a deployment secret store;
- secrets must not be logged;
- secrets must not appear in audit metadata, analytics, outbox payloads, or semantic docs;
- secret rotation must have an explicit deployment/restart plan;
- test/local fake secrets must be clearly scoped and never accepted in production.

## Database and Migration Settings

- Runtime connects to PostgreSQL 18.4 target from [../stack.md](../stack.md).
- Local development defaults to `postgresql+asyncpg://iotables:iotables@localhost:5433/iotables`, backed by the Docker Compose `db` service. This is a local fake credential only.
- Alembic migrations run as a deployment step, not from normal request handling.
- Migration configuration must not import FastAPI routers or runtime providers with side effects.
- The application readiness check must verify the expected migration head.
- Business seed/provisioning data must not run automatically on startup, deployment, migration, or release upgrade.

## Provider Configuration

V1 provider-sensitive areas:

| Area | Rule |
| --- | --- |
| OTP/SMS | Production requires real provider config; local/test may use fake provider. |
| DNS | Manual in the current release; no provider credentials required unless automation is explicitly introduced. |
| Payment provider | Out of the current release; provider config must not appear until the product contract exists. |
| Fiscal/e-Adisyon/ÖKC | Out of the current release; provider config must not appear until explicitly introduced. |

Provider calls that create side effects must use durable outbox/attempt records and must not pretend to roll back automatically.

## Configuration Validation

Startup validation must check:

- required values are present;
- production secrets are not placeholders;
- `IOTABLES_SECURITY_SECRET_KEY` is environment-owned and rotated through an explicit deployment plan;
- secure cookies are enabled in production;
- allowed hosts/origins are explicit;
- database URL points to the intended environment;
- provider fake mode is disabled in production;
- tenant root domain/platform host are consistent;
- TTL/rate-limit values are positive and sane.

## Acceptance

Runtime configuration is acceptable when:

- backend settings are typed and validated before serving traffic;
- frontend config contains no secrets;
- production cannot start with local/test unsafe defaults;
- migration/provisioning/seed behavior is not hidden in app startup;
- provider and secret rules are explicit enough to test.
