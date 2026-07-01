# Implementation Readiness Review

This document records the documentation readiness state before first implementation work begins.

It is not a replacement for app, module, database, API, testing, security, or ops documents. It is the final cross-layer gate that confirms where implementation must read from and what must not be invented in code.

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

## Readiness Status

IoTables documentation is ready to start implementation scaffolding for v1.

This means:

- the six apps are defined as semantic source;
- app happy paths, branch scenarios, UI states, visibility, copy, components, analytics, and tests are documented;
- modules, contracts, APIs, data model, database schema, constraints, transactions, migration/rollback, seed/provisioning, security, testing, and ops policies exist;
- semantic index generation is available and must be regenerated after indexed documentation changes.

This does not mean implementation is complete. It means code should now follow the documented derivation chain instead of inventing behavior.

## Cross-Layer Gate

| Layer | Status | Source |
| --- | --- | --- |
| App semantics | Ready | `docs/apps/{app}/` |
| Module boundaries | Ready | [modules/module-map.md](modules/module-map.md) |
| Data model | Ready | [data-model.md](data-model.md) |
| PostgreSQL schema and constraints | Ready | [database/schema.md](database/schema.md), [database/indexes-constraints.md](database/indexes-constraints.md) |
| Transactions and rollback | Ready | [database/transactions.md](database/transactions.md), [database/migrations.md](database/migrations.md) |
| Seed/provisioning | Ready | [database/seed-provisioning.md](database/seed-provisioning.md), [modules/platform/sector-starter-templates.md](modules/platform/sector-starter-templates.md) |
| API contracts | Ready | [api/README.md](api/README.md), module `*-api.md` files |
| Security | Ready | [security/threat-model.md](security/threat-model.md), [security/rate-limits.md](security/rate-limits.md) |
| Test strategy | Ready | [testing/strategy.md](testing/strategy.md), app `test-plan.md` files |
| Runtime operations | Ready | [ops/configuration.md](ops/configuration.md), [ops/deployment.md](ops/deployment.md), [ops/observability.md](ops/observability.md) |
| Semantic retrieval | Ready | [semantic/source-policy.md](semantic/source-policy.md), [semantic/index.jsonl](semantic/index.jsonl) |

## Implementation Rules

Before implementing any behavior:

1. Start from the owning app scenario.
2. Read the app `definition.md`, `scenarios.md`, `api-usage.md`, `test-plan.md`, and relevant UI package docs.
3. Read the owning module document, contract, and API file.
4. Read the related data, transaction, constraint, security, and test sources.
5. Search [semantic/index.jsonl](semantic/index.jsonl) for related semantic IDs, endpoints, commands, and symbols.
6. Implement the smallest coherent slice across docs, code, tests, and migrations.
7. Regenerate the semantic index when indexed docs change.

If implementation exposes a contradiction, repair the owning documentation first and propagate the correction through downstream layers.

## First Implementation Order

Recommended first implementation sequence:

| Order | Work | Why |
| --- | --- | --- |
| 1 | Repository scaffold for backend/frontend/shared tooling | Establish project shape without business behavior. |
| 2 | Backend configuration, logging, error envelope, auth/session shell | Cross-cutting runtime foundation. |
| 3 | PostgreSQL/Alembic base schema and constraints | Data integrity before feature APIs. |
| 4 | Tenant Registry, Access, Provisioning, Sector Starter Templates | PlatformApp can create tenants safely. |
| 5 | Tenant Setup modules | TenantApp can manage halls, tables, stations, menu, staff, settings. |
| 6 | QR/Table Presence and Customer Ordering | CustomerApp core value path. |
| 7 | Fulfillment modules | StationStaffApp and ServiceStaffApp workflows. |
| 8 | Settlement modules | CashierApp payment/correction/closure workflows. |
| 9 | Analytics/observability surfaces | Derived summaries only after source records exist. |

This order can change for a narrow vertical slice, but the dependency direction must not be inverted.

## Critical Invariants

Implementation must preserve these invariants from day one:

- six apps remain the semantic foundation;
- tenant context is resolved from trusted host/session state;
- tenant name and subdomain are immutable after creation;
- tenant GSM is required for tenant creation and first-password OTP flows;
- tenant admin and cashier first-password setup require OTP;
- station/service staff first-password setup does not require OTP in v1;
- QR tokens are short-lived, one-time, and backend/database enforced;
- CustomerOrderingSession and TableSession remain separate;
- order submit, payments, cashier corrections, starter templates, and bulk delivery are idempotency-safe;
- starter templates run only during tenant creation and exactly once per tenant/template version;
- `cafe.v1` starter product prices come from Sector Starter Templates;
- DeliveryState stores picked-up/delivered only; ready comes from Preparation;
- every TableSession has one Check/Adisyon in v1;
- payment totals and balances are server-calculated;
- closed sessions reject normal orders/payments/corrections;
- audit is immutable evidence, not analytics or rollback state;
- logs, metrics, analytics, audit, and outbox records must not store secrets.

## Non-Blocking Deferred Decisions

These are intentionally not blockers for first implementation:

| Decision | Reason |
| --- | --- |
| Final hosting provider | Deployment policy is provider-neutral. |
| Observability vendor | Docs require safe signals, not a vendor. |
| External payment provider | Out of v1. |
| Fiscal/e-Adisyon/ÖKC provider | Out of v1. |
| Visual floor-plan editor | Out of v1; ordered table grid is locked. |
| Historical BI/reporting | Out of v1; app analytics are derived summaries. |

## Verification Requirement

Before coding starts from this documentation state:

- `python tools/build_semantic_index.py` must succeed;
- `python -m py_compile tools/build_semantic_index.py` must succeed;
- documentation link/index/checklist validation must pass;
- `git diff --check` must pass.

When implementation begins, add executable tests according to [testing/strategy.md](testing/strategy.md) and the owning app `test-plan.md` files.

## Readiness Conclusion

The documentation set is coherent enough to begin implementation.

The next work should be implementation scaffolding, not more feature-definition expansion, unless a new contradiction is discovered.
