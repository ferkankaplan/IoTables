# PlatformApp Test Plan

This document defines PlatformApp-visible test coverage for v1. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

Source context:

- [definition.md](definition.md)
- [end-to-end.md](end-to-end.md)
- [scenarios.md](scenarios.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [wireframes.md](wireframes.md)
- [copy.md](copy.md)
- [components.md](components.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Test Scope

PlatformApp tests prove that the Platform Owner can authenticate, create tenants safely, inspect tenant health, track manual DNS readiness, manage tenant lifecycle, edit audited platform-owned profile fields, and recover failed provisioning without becoming a tenant runtime operator.

Out of scope for this test plan:

- customer order creation;
- station preparation;
- service delivery;
- cashier payment, correction, or close-session mutation;
- tenant admin setup surfaces;
- DNS provider automation;
- payment provider, fiscal, printer, terminal, cash drawer, or offline POS setup.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| P-01 Platform Owner Login | Platform Owner completes username/password login before dashboard access. |
| P-02 Create Tenant With Cafe Starter | Required tenant identity is submitted, provisioning applies `cafe.v1` once, tenant becomes active, and DNS checklist remains manual. |
| P-03 Manual DNS Readiness | Platform Owner marks DNS readiness and tenant health reflects the manual flag. |
| P-04 Suspend and Reactivate Tenant | Platform Owner suspends/reactivates with reason and tenant runtime availability follows lifecycle state. |
| P-05 List and Inspect Tenants | Dashboard/list/detail show platform-owned metadata, lifecycle, setup, starter, and high-level health. |
| P-06 Update Tenant GSM | GSM update validates, audits, and affects future OTP targets only. |

## Branch Coverage

### Login and Access

| Branch | Expected Test Result |
| --- | --- |
| First Platform Owner missing | Dashboard unavailable; setup unavailable copy shown. |
| Bootstrap password still active | Password change required before dashboard. |
| Invalid credentials | Safe rejection; no tenant data exposed. |
| Platform user disabled | Safe rejection; no tenant data exposed. |
| Tenant user attempts PlatformApp | Wrong app scope; no tenant data exposed. |

### Tenant Creation and Provisioning

| Branch | Expected Test Result |
| --- | --- |
| Tenant name missing | Field error; provisioning not started. |
| Subdomain missing | Field error; provisioning not started. |
| GSM missing | Field error; provisioning not started. |
| Subdomain duplicate | Field error; no second tenant created. |
| Duplicate tenant name with unique subdomain | Allowed. |
| Unsupported sector | Field error; provisioning not started. |
| Sector omitted | Tenant created without starter data unless future app rules require sector. |
| Same idempotency key and same request | Original provisioning result is shown. |
| Same idempotency key and different request | Conflict is shown; no parallel tenant. |
| Starter application already exists | Starter data is not reapplied. |
| Starter data failure | Tenant not activated; failure state visible and recoverable. |
| Tenant admin creation failure | Tenant not activated; failure state visible and recoverable. |
| Audit failure for critical event | Tenant creation fails or enters recoverable failure according to audit policy. |

### DNS, Lifecycle, and Settings

| Branch | Expected Test Result |
| --- | --- |
| DNS readiness not marked | Health shows DNS not ready; tenant runtime mutation is not implied. |
| DNS readiness changed incorrectly | Change is recorded; correction is another audited update. |
| Suspend without reason | Rejected with reason-required message. |
| Tenant already suspended | Current suspended state is returned or shown idempotently. |
| Reactivate invalid transition | Rejected with safe lifecycle error. |
| Tenant state stale in detail panel | Sensitive actions disabled until refresh. |
| GSM invalid | Field error; no change. |
| Same GSM submitted | No-op/idempotent result; audit behavior follows backend rule. |
| Active OTP exists for old GSM | Existing challenge target does not silently change; future challenge uses new GSM. |
| Sector changed after creation | Starter data does not rerun. |

### Listing, Detail, Audit, and Visibility

| Branch | Expected Test Result |
| --- | --- |
| Empty tenant list | Empty state exposes create tenant action. |
| Partial health unavailable | Identity metadata remains visible with unknown/degraded summary. |
| Tenant provisioning failed | Detail shows failure and recovery affordance when available. |
| Tenant suspended | Detail shows suspended state and reason where allowed. |
| Tenant not found/hidden | Safe not-found state; no record leakage. |
| Audit empty | Audit empty state appears. |
| Audit filtered empty | Filtered empty state appears. |
| Runtime health signal unavailable | Platform metadata view still works. |
| Platform attempts tenant runtime mutation | UI control absent and API rejects wrong scope. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Platform Owner must log in before seeing tenants | Browser and API auth tests. |
| First Platform Owner bootstrap is explicit and one-time | Bootstrap/ops test plus login unavailable state. |
| Platform Owner login does not require OTP/TOTP in v1 | Browser login gate tests. |
| Tenant creation requires name, subdomain, and GSM | Form validation and API contract tests. |
| Tenant starts as `provisioning` | Provisioning API/domain tests. |
| Tenant becomes `active` only after required setup records commit | Transaction/integration tests. |
| Provisioning failure is visible and recoverable | Browser, API, and recovery tests. |
| Starter template is applied exactly once | Database/integration/idempotency tests. |
| Manual DNS readiness is trackable but not automated | Browser and API tests; no DNS provider side effect. |
| PlatformApp cannot mutate tenant runtime orders/payments/sessions/preparation/delivery | Negative UI and API authorization tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| Login | loading, invalid credentials, first password change required |
| Dashboard / Tenant List | loading, empty tenant list, partial health unavailable, tenant row stale, platform auth expired |
| Create Tenant | pristine, validating, submitting, provisioning, provisioning failed, success |
| Tenant Detail | loading, not found, suspended, provisioning, provisioning failed, DNS not ready, health unavailable |
| Tenant Audit | loading, empty audit, filtered empty, access denied |

## API Usage Coverage

PlatformApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/v1/auth/login-requirements` | Bootstrap/setup requirements are safe and do not expose tenant data. |
| `POST /api/v1/auth/login` | Platform Owner login, wrong app scope, invalid credentials. |
| `GET /api/v1/auth/session` | Protected route access and auth-expired behavior. |
| `POST /api/v1/auth/logout` | Session revoked and dashboard hidden. |
| `POST /api/v1/auth/totp/enroll` | Reserved for future PlatformApp hardening; not required by v1 login. |
| `GET /api/v1/platform/tenants` | List/health filters, partial health, no runtime leakage. |
| `GET /api/v1/platform/tenants/{tenantId}` | Detail visibility and not-found/hidden behavior. |
| `PATCH /api/v1/platform/tenants/{tenantId}/profile` | GSM/sector/capacity/address update, immutable identity rejection. |
| `POST /api/v1/platform/tenants` | Create tenant idempotency, required fields, duplicate subdomain, provisioning result. |
| `GET /api/v1/platform/tenants/{tenantId}/provisioning` | Safe provisioning state and failure summary. |
| `GET /api/v1/platform/tenants/{tenantId}/provisioning/recovery-summary` | Safe recovery summary only. |
| `POST /api/v1/platform/tenants/{tenantId}/provisioning/retry` | Retry allowed state, no starter rerun, stale/failure cases. |
| `GET /api/v1/platform/sectors` | Supported sector options. |
| `GET /api/v1/platform/sectors/{sector}/starter-template` | Starter preview only; no template mutation. |
| `GET /api/v1/platform/tenants/{tenantId}/starter-template-application` | Starter application state. |
| `POST /api/v1/platform/tenants/{tenantId}/dns-ready` | Manual DNS flag update and audit expectation. |
| `POST /api/v1/platform/tenants/{tenantId}/status` | Suspend/reactivate with reason and lifecycle validation. |
| `GET /api/v1/platform/tenants/{tenantId}/lifecycle-events` | Selected tenant lifecycle timeline without runtime detail leakage. |
| `GET /api/v1/platform/audit-events` | Redacted platform audit events only. |
| `GET /api/v1/platform/side-effects/failed` | Recovery visibility only; no raw provider payloads. |

## Security and Abuse Coverage

Required tests:

- no tenant data is rendered before authenticated Platform Owner session;
- tenant users and staff sessions cannot access PlatformApp;
- Platform session cannot call tenant runtime mutation APIs;
- unsafe PlatformApp requests require CSRF;
- create tenant requires `Idempotency-Key`;
- normalized subdomain uniqueness is enforced even under concurrent create attempts;
- tenant name and subdomain cannot be changed after creation;
- tenant GSM changes are audited and do not alter already-issued OTP targets;
- starter template application is unique per tenant/template/version and does not rerun on restart, deployment, migration, retry, or sector edit;
- provisioning failure leaves no silent active tenant with partial required setup;
- platform audit and side-effect views redact raw OTP, secrets, provider payloads, internal paths, and stack traces.

## Accessibility and Responsive Coverage

Required checks:

- login, TOTP, tenant creation, settings save, DNS readiness, suspend/reactivate, audit, and provisioning retry work by keyboard;
- drawers and dialogs trap and restore focus;
- status badges and health flags have text alternatives;
- tenant table/list row focus and selected state are visible;
- mobile fallback keeps tenant list readable and create/detail drawers usable;
- tablet and desktop layouts avoid overlapping tenant names, domains, failure summaries, badges, and action controls;
- destructive/sensitive dialogs identify the tenant and reason requirement.

## Copy Coverage

Tests must assert that:

- login/setup failures use [copy.md](copy.md) and reveal no tenant data before auth;
- tenant creation copy marks name, subdomain, and GSM as required;
- immutable identity copy appears for tenant name/subdomain;
- sector copy says starter data does not rerun after creation;
- DNS copy says manual readiness and does not imply automation;
- lifecycle dialogs mention reason/audit consequences;
- forbidden platform claims and runtime action labels from [copy.md](copy.md) are absent.

## Forbidden Control Coverage

PlatformApp tests must prove these controls are absent:

- create customer order;
- prepare or deliver item;
- receive, void, or provider-process payment;
- close table session;
- edit customer cart;
- mutate station queue;
- DNS provider automation;
- fiscal/e-Adisyon/ÖKC setup;
- external payment provider setup;
- printer, terminal, cash drawer, or offline POS setup.

## Traceability

When implementation begins:

- browser E2E tests should reference PlatformApp scenarios P-01 through P-06;
- API tests should reference [api-usage.md](api-usage.md) and module API contracts;
- provisioning idempotency/race/rollback tests should reference database transaction and seed/provisioning sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

PlatformApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- tenant creation idempotency, starter one-time application, and provisioning rollback coverage are defined;
- auth/TOTP and wrong-scope abuse coverage are defined;
- UI state and copy coverage are defined;
- forbidden PlatformApp runtime controls are explicitly tested absent;
- semantic index is regenerated after this document changes.
