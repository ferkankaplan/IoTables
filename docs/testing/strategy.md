# Test Strategy

This document defines the shared current release test strategy for IoTables.

It does not replace app `test-plan.md` files or module-specific transaction tests. It defines how tests are derived, where they belong, and which risks must be covered before implementation is considered complete.

Source context:

- [../semantic/source-policy.md](../semantic/source-policy.md)
- [../apps/_shared/branch-coverage-checklist.md](../apps/_shared/branch-coverage-checklist.md)
- [../apps/_shared/wireframe-rules.md](../apps/_shared/wireframe-rules.md)
- [../modules/README.md](../modules/README.md)
- [../database/transactions.md](../database/transactions.md)
- [../database/indexes-constraints.md](../database/indexes-constraints.md)
- [../api/auth.md](../api/auth.md)
- [../api/errors.md](../api/errors.md)
- [../api/idempotency.md](../api/idempotency.md)
- [../security/threat-model.md](../security/threat-model.md)
- [../security/rate-limits.md](../security/rate-limits.md)

## Source Order

Tests follow the semantic derivation chain:

1. App scenario and acceptance criteria.
2. App branch, UI state, visibility, and copy/accessibility expectations.
3. Module command/query contracts and permission policy.
4. Data model, database constraints, transaction, rollback, and concurrency rules.
5. API request/response, auth, idempotency, and error contracts.
6. Implementation behavior.

If a test exposes a product ambiguity, fix the owning app or module documentation first. Do not encode new product rules only in tests.

## Test Ownership

| Test Document / Location | Owns |
| --- | --- |
| `docs/testing/strategy.md` | Shared test taxonomy, risk coverage rules, and traceability rules. |
| `docs/apps/{app}/test-plan.md` | App-visible happy paths, branch flows, UI states, accessibility checks, and acceptance criteria. |
| Module documents | Module-specific invariant, command/query, security, concurrency, rollback, and side-effect notes when shared strategy is not enough. |
| `docs/database/transactions.md` | Critical transaction, lock ordering, idempotency, rollback, and race test requirements. |
| `docs/api/*.md` and module `*-api.md` | API envelope, auth, error, idempotency, and request/response contract tests. |
| Implementation test files | Executable proof linked back to semantic source; implementation tests must not redefine behavior. |

Add module-owned test notes only when a module has special concurrency, security, rollback, or side-effect behavior that cannot be expressed by the shared strategy and transaction catalog.

## Test Layers

| Layer | Purpose | Required Coverage |
| --- | --- | --- |
| Documentation consistency tests | Keep app, module, data, API, and index records synchronized. | Links, semantic index freshness, endpoint coverage, module doc triplets, checklist exclusion. |
| Domain/unit tests | Prove pure business rules without HTTP/UI. | State transitions, validation, price snapshot rules, visibility mapping, failure names. |
| Database/integration tests | Prove persistence invariants. | Unique constraints, composite tenant FKs, check constraints, lock/race behavior, rollback. |
| API contract tests | Prove app-facing HTTP behavior. | Auth, CSRF, idempotency, error envelope, status codes, safe messages, request/response shape. |
| Frontend/component tests | Prove app UI behavior before browser E2E. | State rendering, pending buttons, stale/error handling, visibility, copy, accessibility basics. |
| Browser E2E tests | Prove user workflows across app surfaces. | Happy paths, major branches, QR/order/payment/session flows, context preservation. |
| Security abuse tests | Prove fail-closed controls. | Cross-tenant access, wrong app scope, QR replay, OTP abuse, customer price tampering, CSRF. |
| Worker/side-effect tests | Prove reliable external work. | Outbox claim, retry, stale claim recovery, redaction, duplicate effect protection. |

## Minimum App Test Plan Contents

Every app `test-plan.md` must include:

- happy path coverage mapped to `end-to-end.md`;
- branch coverage mapped to `scenarios.md`;
- acceptance criteria coverage;
- UI state coverage mapped to `ui-states.md`;
- visibility coverage mapped to `visibility.md`;
- API usage coverage mapped to `api-usage.md`;
- accessibility and responsive checks from [../apps/_shared/accessibility-responsive.md](../apps/_shared/accessibility-responsive.md);
- copy checks from [../apps/_shared/copy-style.md](../apps/_shared/copy-style.md);
- out-of-scope controls that must not appear.

## Branch Coverage Rule

Each endpoint, command, or UI mutating action must cover:

- happy path;
- invalid input branch;
- unauthorized or wrong-scope branch;
- stale state branch;
- duplicate/idempotent retry branch where applicable;
- concurrent mutation branch where applicable;
- transaction failure behavior where applicable;
- visible app outcome.

This rule comes from [../apps/_shared/branch-coverage-checklist.md](../apps/_shared/branch-coverage-checklist.md). App test plans may add stricter branch coverage, but they may not weaken this minimum.

## Critical Risk Coverage

### Tenant and Access

Required tests:

- Platform session cannot call tenant runtime mutation APIs.
- Tenant staff session cannot cross tenant host or tenant-owned IDs.
- Wrong app scope returns safe failure.
- Disabled user/role/station/hall assignment fails at mutation time.
- Tenant creation requires OTP to the platform-owned tenant identity GSM; tenant admin, cashier, station, and service first-password setup do not require OTP in the current release.
- Platform Owner does not require OTP/TOTP before PlatformApp dashboard access in the current release.

### QR Presence and Customer Ordering

Required tests:

- Expired, consumed, wrong-table, and concurrent QR token redemption fail closed.
- Fresh presence is required for order submit, table orders, bill summary, and payment summary.
- Cart survives fresh QR re-verification while CustomerOrderingSession remains valid.
- CustomerOrderingSession can submit multiple orders.
- Duplicate order submit returns the original order result.
- Same idempotency key with different cart/request returns conflict.
- Failed order submit preserves cart and creates no partial order, queue item, Check, or audit event.
- Client-supplied price, total, station, tenant, or table authority is ignored.

### Tenant Setup and Provisioning

Required tests:

- Tenant name, subdomain, and GSM are required at creation.
- Tenant name and subdomain are immutable after creation.
- Starter template applies exactly once per tenant.
- Starter template does not rerun on restart, deployment, migration, retry, or sector/profile edit.
- Failed provisioning leaves safe recovery state.
- Tables remain managed in hall context; standalone table management is not exposed as a primary UI.
- Table display claim consumption and credential rotation are atomic.

### Fulfillment

Required tests:

- Station staff can mutate only assigned station queue items.
- Preparation transitions reject stale status changes.
- `cannot_prepare` requires a reason.
- Service staff can mutate only authorized hall items.
- Service tracking disabled hides/blocks ServiceStaffApp mutation controls.
- Bulk delivery is all-or-nothing and same-table scoped.
- DeliveryState never stores `ready`; ready state comes from PreparationItem.

### Settlement

Required tests:

- Cashier sees active table sessions and server-calculated balances only for own tenant.
- Payment amount must be positive and not exceed remaining balance.
- Duplicate payment submit returns the original payment.
- Concurrent payments recompute remaining balance under Check lock.
- Session close requires zero remaining balance and is explicit.
- Closed sessions reject new orders, payments, corrections, and fulfillment mutation except explicit recovery.
- Corrections require reason, idempotency, target eligibility, and audit.
- Item void is allowed only while preparation is `pending` or `cannot_prepare` and before any payment on the Check.
- Non-provider payment void is allowed only on open Check in the current release.

### Reliable Side Effects

Required tests:

- Side effect is not executed before source transaction commits.
- Outbox enqueue uses stable idempotency reference.
- Parallel workers do not claim the same message.
- Expired claims are recoverable.
- Provider failure records redacted attempt state.
- Duplicate enqueue returns existing effect or duplicate failure without creating another effect.
- Raw OTP, QR, credential, session, provider secret, or sensitive payload is not stored in outbox/audit records.

## API Contract Coverage

Every module-owned API endpoint test must verify:

- method and route shape;
- request body/query/path validation;
- authenticated actor and app scope;
- CSRF on unsafe cookie-auth requests;
- tenant resolution from trusted host/session context, not body/query tenant IDs;
- idempotency header requirement when listed in [../api/idempotency.md](../api/idempotency.md);
- successful response schema;
- standard error envelope from [../api/errors.md](../api/errors.md);
- safe user-facing error message;
- no raw secrets or internal paths in responses.

## Frontend Test Coverage

Every app UI package must verify:

- primary workspaces and contextual overlays preserve user context;
- pending buttons disable without becoming the only duplicate defense;
- stale state disables unsafe actions and offers refresh/retry;
- app-visible copy does not expose internal security terms;
- forbidden/out-of-scope controls are absent;
- keyboard focus works through panels, drawers, dialogs, and bottom sheets;
- small mobile, tablet, and desktop layouts avoid overlapping text and controls;
- customer QR retry and cart preservation behavior are visible;
- operational touch targets meet the shared minimum.

## Traceability

Executable tests should reference semantic source by path or `semantic_id` when implementation begins.

Rules:

- Reference the highest owning source that defines the behavior.
- Prefer app scenario or module contract IDs for behavior tests.
- Prefer transaction catalog IDs for race/rollback tests.
- Prefer API contract IDs for HTTP envelope tests.
- Do not put product behavior only in test names or comments.
- If a source document changes, affected tests must be reviewed in the same change.

## Acceptance Gate

A feature is not implementation-ready until:

- app scenario and acceptance criteria exist;
- module contract exists for owned commands/queries;
- data and transaction rules exist for persistence-changing behavior;
- API contract exists for app-facing endpoints;
- test ownership is clear;
- required branch and risk coverage are documented;
- semantic index is regenerated when indexed docs changed.

## Open Questions

None currently.
