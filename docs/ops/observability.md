# Runtime Observability

This document defines current release runtime observability expectations for IoTables. It does not define product analytics, audit evidence, or a vendor-specific monitoring stack.

Source context:

- [../stack.md](../stack.md)
- [../api/errors.md](../api/errors.md)
- [../security/threat-model.md](../security/threat-model.md)
- [../security/rate-limits.md](../security/rate-limits.md)
- [../modules/governance/audit.md](../modules/governance/audit.md)
- [../modules/governance/reliable-side-effects.md](../modules/governance/reliable-side-effects.md)
- [../database/transactions.md](../database/transactions.md)
- [../database/seed-provisioning.md](../database/seed-provisioning.md)
- [../testing/strategy.md](../testing/strategy.md)

## Purpose

Observability exists to answer operational questions:

- is the platform healthy;
- are APIs failing;
- are database transactions safe and performant;
- are one-time/idempotent flows behaving correctly;
- are external side effects retrying or failing;
- are tenants isolated and scoped correctly.

Observability must not become:

- immutable audit evidence;
- product analytics source of truth;
- business state authority;
- a place to store secrets or sensitive payloads.

## Signals

| Signal | Current Release Expectation |
| --- | --- |
| Logs | Structured application logs with request/tenant/app/module context where safe. |
| Metrics | Counters, gauges, and timings for runtime health and safety paths. |
| Traces | Request/module spans when implementation adds tracing support. |
| Health checks | Safe readiness/liveness checks for app, database, migrations, and workers. |
| Audit | Separate append-only business/security evidence in Governance/Audit. |
| Analytics | Separate app-owned product/operational summaries in app analytics docs. |

The current release does not lock a vendor. Implementation may use local logs and later add OpenTelemetry-compatible instrumentation without changing product semantics.

## Structured Logging

Every backend request log should include safe context when available:

| Field | Notes |
| --- | --- |
| `requestId` | Generated per inbound request. |
| `correlationId` | Propagated across outbox/workers when available. |
| `tenantId` | Safe UUID only when resolved. |
| `appScope` | PlatformApp, TenantApp, CustomerApp, StationStaffApp, ServiceStaffApp, CashierApp. |
| `actorType` | platform_owner, tenant_user, customer_session, display_device, system. |
| `module` | Owning module/context handling the operation. |
| `route` | Route template, not raw URL with secrets. |
| `statusCode` | HTTP result. |
| `errorCode` | API error code when present. |
| `durationMs` | Request duration. |

Logs must never include:

- passwords;
- OTP codes;
- raw QR tokens;
- raw display credentials;
- session cookies;
- TOTP secrets;
- payment provider secrets;
- raw provider payloads;
- stack traces in user-facing responses.

## Required Runtime Metrics

| Area | Metrics |
| --- | --- |
| HTTP API | request count, latency, error count by route/app/error code. |
| Auth/session | login failures, wrong app scope, session expiry, CSRF failures, rate-limit hits. |
| OTP | challenge created, send success/failure, verify success/failure, locked/expired. |
| QR/table presence | token issued, redeemed, expired, consumed/replay rejected. |
| Order submit | submit attempts, accepted, idempotent replay, conflict/rejected, transaction failure. |
| Fulfillment | preparation transition failures, delivery transition failures, bulk idempotency conflicts. |
| Settlement | payment recorded, overpayment rejected, payment idempotent replay, correction rejected, close rejected. |
| Provisioning | tenant create attempts, starter template applied, failed stage, recovery state. |
| Outbox/side effects | queued, sent, retryable failure, permanent failure, oldest pending age. |
| Database | connection pool saturation, transaction errors, lock timeouts, migration head mismatch. |
| Semantic tooling | semantic index build failure in documentation workflow. |

Metrics labels must avoid high-cardinality raw user input. Use route templates, module names, app scopes, status/error codes, and safe enum values.

## Health Checks

| Check | Meaning | Must Not Expose |
| --- | --- | --- |
| App liveness | Process can respond. | Config secrets or stack traces. |
| App readiness | Required config loaded, DB reachable, migrations at expected head. | Raw database URL. |
| Database readiness | PostgreSQL connection and basic query succeed. | Credentials. |
| Outbox readiness | Worker can read pending side effects. | Provider secrets. |
| Tenant health summary | Platform-visible safe tenant state. | Tenant runtime orders/payments/session details. |

PlatformApp tenant health remains high-level and must not inspect tenant runtime detail unless a future support workflow explicitly allows it.

## Error Correlation

- Every API error response should include a safe `requestId`.
- Internal logs may include exception class and sanitized context.
- User-facing API responses must use standard error envelopes and safe messages from [../api/errors.md](../api/errors.md).
- For idempotency conflicts, logs should include module, command, target type, and conflict code, not request bodies with sensitive fields.

## Alerts

V1 alert rules should exist for:

- API error rate above expected baseline;
- database unavailable;
- migration head mismatch;
- outbox oldest pending age above threshold;
- OTP delivery failure spike;
- QR redemption replay/expired spike;
- order/payment idempotency conflict spike;
- provisioning failures;
- audit write failure for critical actions.

Exact thresholds are environment-specific and must be configured outside source code.

## Retention

| Data | Retention Rule |
| --- | --- |
| Audit events | Indefinite in the current release unless explicit retention policy is introduced. |
| Application logs | Environment policy; never source of business truth. |
| Metrics | Environment policy; aggregate only. |
| Traces | Short operational retention. |
| Outbox attempts | Follow reliable side-effect recovery needs. |

## Acceptance

Runtime observability is acceptable when:

- all critical user/business flows produce safe logs and metrics;
- secrets are redacted by default and covered by tests;
- audit, analytics, and observability remain separate;
- health checks prove readiness without leaking internals;
- failures can be correlated by request/correlation ID.
