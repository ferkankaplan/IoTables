# Implementation Roadmap Review

This document records the current implementation review for IoTables v1.

It is not a product source of truth by itself. Product behavior remains owned by app documents, module contracts, the data model, database documents, API contracts, and tests. This file summarizes implementation status and the next execution order after the first vertical slices were built.

Source context:

- [semantic/source-policy.md](semantic/source-policy.md)
- [apps/README.md](apps/README.md)
- [modules/module-map.md](modules/module-map.md)
- [data-model.md](data-model.md)
- [database/schema.md](database/schema.md)
- [database/indexes-constraints.md](database/indexes-constraints.md)
- [database/transactions.md](database/transactions.md)
- [api/README.md](api/README.md)
- [testing/strategy.md](testing/strategy.md)
- [security/threat-model.md](security/threat-model.md)
- [ops/configuration.md](ops/configuration.md)
- [ops/deployment.md](ops/deployment.md)
- [ops/observability.md](ops/observability.md)
- [semantic/index.jsonl](semantic/index.jsonl)

## Current Status

IoTables has moved past documentation readiness and initial scaffolding. The project now has a working v1 vertical implementation across the six app surfaces:

- PlatformApp can authenticate a platform owner and create/manage tenants through tenant registry and provisioning flows.
- TenantApp can authenticate tenant staff and manage tenant profile, halls, tables, stations, menu catalog, availability, and table display provisioning.
- CustomerApp can use QR/table presence, browse menu, manage cart, and submit orders with idempotency protection.
- StationStaffApp can read preparation queue and transition preparation items through `pending`, `preparing`, `ready`, and `cannot_prepare`.
- ServiceStaffApp can read ready service queue, pick up, deliver, and bulk deliver same-table items with idempotency protection.
- CashierApp can read venue board, view table-session orders, read bill summary, record payments, void payments with correction/audit evidence, and close fully paid sessions.

The implementation is not production-complete. The next roadmap is about hardening, closing known app gaps, and reducing runtime risk without changing the six-app semantic foundation.

## Cross-Layer Status

| Layer | Status | Notes |
| --- | --- | --- |
| App semantics | Stable | Six apps remain the semantic foundation. |
| Module boundaries | Implemented in first slices | Platform, tenant setup, ordering, fulfillment, and settlement packages now exist in code. |
| Data model | Implemented as SQLAlchemy metadata | Several runtime tables and constraints are represented in `src/iotables/database/schema.py`. |
| Migrations | Partial | Initial and extension migrations exist, but migration coverage needs a fresh audit against current metadata. |
| API contracts | Partially implemented | Main happy-path APIs exist; some documented list/history/correction endpoints remain. |
| Frontend | Functional first slices | Core app surfaces are present in one SPA; component decomposition remains a cleanup need. |
| Tests | Good API and schema coverage | Current suite covers API boundaries and schema constraints; deeper DB transaction/concurrency tests remain. |
| Semantic index | Available | Regenerate after indexed documentation changes. |
| Ops | Documented, partially implemented | Local DB/dev commands exist; production runtime, observability, and side-effect workers remain. |

## Implemented Vertical Slices

| Slice | Main Evidence |
| --- | --- |
| Platform owner auth and tenant lifecycle | `src/iotables/api/platform.py`, `src/iotables/modules/platform/`, `tests/test_platform_provisioning_api.py` |
| Tenant admin setup surfaces | `src/iotables/api/tenant_setup.py`, `src/iotables/modules/tenant_setup/`, `tests/test_tenant_setup_api.py` |
| QR presence and customer ordering | `src/iotables/api/customer.py`, `src/iotables/api/table_display.py`, `src/iotables/modules/ordering/`, `tests/test_customer_api.py`, `tests/test_table_display_api.py` |
| Station preparation | `src/iotables/api/station_staff.py`, `src/iotables/modules/fulfillment/preparation.py`, `tests/test_station_staff_api.py` |
| Service delivery | `src/iotables/api/service_staff.py`, `src/iotables/modules/fulfillment/service_delivery.py`, `tests/test_service_staff_api.py` |
| Cashier settlement | `src/iotables/api/cashier.py`, `src/iotables/modules/settlement/`, `tests/test_cashier_api.py` |
| Shared auth/session/setup tokens | `src/iotables/api/auth.py`, `src/iotables/modules/access/`, `tests/test_auth_api.py` |

## Review Findings

| Finding | Impact | Roadmap Action |
| --- | --- | --- |
| Frontend is concentrated in `frontend/src/App.tsx`. | Fast for first slice, but hard to maintain and review. | Split by app surface and shared components after runtime gaps are closed. |
| Tenant workspace placeholder copy still appears for areas not fully wired. | Can mislead during manual testing. | Replace stale generic placeholders with accurate per-workspace status or implemented panels. |
| Runtime APIs are mostly happy-path and boundary tested. | Concurrency/idempotency defects may survive API fake-service tests. | Add DB-backed transaction tests for order submit, payment record/void, session close, preparation, and delivery transitions. |
| Some documented endpoints remain unimplemented. | Product docs and runtime surface can drift. | Track endpoint parity in the checklist and implement or explicitly defer. |
| Audit history is written for sensitive commands but not exposed in every app surface. | Operators cannot yet inspect all evidence in-app. | Add Cashier/Tenant operational audit views where documented. |
| Reliable side-effects/outbox are documented but not yet used by workers. | SMS/provider/device reliability is incomplete beyond local records. | Implement worker claim/retry loop before real external integrations. |
| Migration state needs a fresh metadata-to-migration audit. | Local schema may pass while migration order drifts. | Run and repair Alembic upgrade/downgrade checks against a clean database. |

## Roadmap Order

The next work should proceed in this order:

1. Migration and DB integrity audit.
2. Runtime gap closure for documented v1 endpoints.
3. DB-backed transaction and concurrency tests.
4. Frontend decomposition and stale UI copy cleanup.
5. Operational audit/history surfaces.
6. Reliable side-effects worker and provider adapters.
7. Production hardening: configuration, observability, deployment, and smoke tests.
8. Final end-to-end restaurant scenario validation.

This order preserves the dependency chain: database truth first, app-visible gaps second, proof third, maintainability fourth, operations last.

## Critical Invariants

Implementation must continue preserving these invariants:

- six apps remain the semantic foundation;
- tenant context is resolved from trusted host/session state;
- tenant name and subdomain are immutable after creation;
- tenant GSM is required for tenant creation and tenant-admin/cashier first-password OTP flows;
- station/service staff first-password setup does not require OTP in v1;
- QR tokens are short-lived, one-time, and backend/database enforced;
- CustomerOrderingSession and TableSession remain separate;
- order submit, payments, payment voids, cashier corrections, starter templates, and bulk delivery are idempotency-safe;
- starter templates run only during tenant creation and exactly once per tenant/template version;
- `cafe.v1` starter product prices come from Sector Starter Templates;
- DeliveryState stores picked-up/delivered only; ready comes from Preparation;
- every TableSession has one Check/Adisyon in v1;
- payment totals and balances are server-calculated;
- closed sessions reject normal orders/payments/corrections;
- audit is immutable evidence, not analytics or rollback state;
- logs, metrics, analytics, audit, and outbox records must not store secrets.

## Deferred Decisions

These remain intentionally deferred unless the user changes v1 scope:

| Decision | Reason |
| --- | --- |
| Final hosting provider | Deployment policy is provider-neutral. |
| Observability vendor | Docs require safe signals, not a vendor. |
| External payment provider | Out of v1. |
| Fiscal/e-Adisyon/ÖKC provider | Out of v1. |
| Visual floor-plan editor | Out of v1; ordered table grid is locked. |
| Historical BI/reporting | Out of v1; app analytics are derived summaries. |

## Verification Gate

Before declaring v1 implementation complete:

- `pnpm -w run check` must pass;
- `git diff --check` must pass;
- migrations must upgrade a clean database to head;
- downgrade/rollback behavior must be explicitly accepted or tested for each migration class;
- semantic index must be regenerated after indexed documentation changes;
- documented v1 endpoints must be implemented or explicitly deferred in the checklist;
- at least one end-to-end restaurant scenario must run through PlatformApp -> TenantApp -> CustomerApp -> StationStaffApp -> ServiceStaffApp -> CashierApp.
