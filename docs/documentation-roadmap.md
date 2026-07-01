# Documentation Roadmap

This roadmap defines what should be documented next, where each document belongs, and which items are v1-critical versus deferred or intentionally excluded.

The goal is to keep documentation architectural, not decorative. App documents describe user-facing behavior. Module documents describe ownership, invariants, contracts, and operational correctness.

## Placement Rules

| Documentation Type | Primary Location | Rule |
| --- | --- | --- |
| User-facing behavior | `docs/apps/{app}/` | Screens, flows, UI states, copy, app-level analytics, accessibility, responsive behavior, and app E2E tests live with the app. |
| Domain model and business rules | `docs/modules/{context}/{module}.md` | Aggregates, invariants, commands, queries, permissions, transactions, idempotency, module tests, and events live with the owning module. |
| Global domain map | `docs/data-model.md` | Cross-module model map, shared constraints, and system-level transaction boundaries. It must not replace module-owned detail. |
| API standards | `docs/api/` | Shared error shape, idempotency headers, pagination/filtering/sorting, authentication conventions, and response envelope decisions. |
| Detailed API contracts | Owning module folder | Request/response schemas belong beside the module that owns the command/query. If large, use `{module}-api.md`. |
| App API usage | `docs/apps/{app}/api-usage.md` | Apps list which module contracts they use. They do not own the API contract. |
| Database strategy | `docs/database/` | Physical PostgreSQL schema, indexes, constraints, migrations, rollback, and seed/provisioning database rules. |
| Generated semantic index | `docs/semantic/index.jsonl` | Rebuildable search and traceability cache generated from Markdown. It is not a source of truth. |
| Cross-app UI standards | `docs/apps/_shared/` | Shared accessibility, responsive, interaction, copy tone, and UI foundation rules. |
| Security standards | `docs/security/` | Threat model, rate limits, sensitive data rules, session/cookie rules, QR abuse cases, and OTP abuse controls. |
| Operations standards | `docs/ops/` | Environment variables, deployment, observability, backups, retention, and runtime operations. |
| Architecture decisions | `docs/adr/` | Only major decisions with long-term cost or hard-to-reverse consequences. |

## Scope Tiers

| Tier | Meaning |
| --- | --- |
| V1 Required | Must be documented before schema/API/backend/frontend implementation. |
| V1 Lean | Document minimally for v1; do not build a heavy framework around it. |
| V2 | Useful, but not needed for the first coherent implementation. |
| V3 | Future product maturity, scale, or enterprise work. |
| Do Not Document Now | Overengineering or contradicts the current modular monolith/product scope. |

## Current Position

Completed documentation layers:

- module-owned data model detail;
- PostgreSQL schema, indexes, constraints, migration, rollback, seed, and provisioning strategy;
- module command/query contracts;
- permission policy matrix;
- shared API standards;
- module-owned API request/response contracts;
- app API usage maps;
- generated semantic JSONL index for documentation search and later code/test traceability;
- transaction and concurrency catalog for critical v1 flows;
- security threat model and rate limit strategy.

Next layer:

- app wireframes for primary pages, drawers, dialogs, panels, and empty/error states.

## Ordered Work List

| Order | Work Item | Tier | Where To Document | Output |
| --- | --- | --- | --- | --- |
| 1 | Module-owned data model detail | V1 Required | `docs/modules/{context}/{module}.md` plus `docs/data-model.md` summary | Every model has owner, fields, lifecycle, invariants, DB constraints, and deletion/history rule. |
| 2 | PostgreSQL schema design | V1 Required | `docs/database/schema.md` and `docs/database/indexes-constraints.md` | Tables, columns, enums, foreign keys, unique constraints, checks, partial indexes, and ownership mapping. |
| 3 | Migration and rollback strategy | V1 Required | `docs/database/migrations.md` | Alembic policy, rollback expectations, data migrations, one-time business migrations, and unsafe-change rules. |
| 4 | Seed and provisioning strategy | V1 Required | `docs/modules/platform/provisioning.md`, `docs/modules/platform/sector-starter-templates.md`, `docs/database/seed-provisioning.md` | Tenant creation transaction, starter template idempotency, recovery states, and no-rerun guarantees. |
| 5 | Module command/query contracts | V1 Required | Owning module docs; split to `{module}-contracts.md` only when too large | Commands, queries, actors, guards, validation, transaction boundaries, idempotency, and returned domain results. |
| 6 | Permission policy matrix | V1 Required | `docs/modules/access/staff-access.md`, `docs/modules/access/identity-access.md`, and app visibility docs | Who may execute each command and which scope checks are enforced server-side. |
| 7 | API standards | V1 Required | `docs/api/README.md`, `docs/api/errors.md`, `docs/api/idempotency.md`, `docs/api/pagination-filtering.md` | Shared API conventions before endpoint-specific contracts are written. |
| 8 | API request/response contracts | V1 Required | Owning module folder, with app references in `docs/apps/{app}/api-usage.md` | Endpoint/command schemas, status codes, error cases, idempotency behavior, and examples. |
| 9 | Transaction and concurrency catalog | V1 Required | Module docs plus `docs/database/transactions.md` | Locking/version strategy for tenant creation, QR redeem, order submit, payment, correction, delivery, and close-session. |
| 10 | Security threat model | V1 Required | `docs/security/threat-model.md` | QR abuse, fake orders, OTP abuse, tenant isolation, session theft, duplicate submit, cashier/payment misuse. |
| 11 | Rate limit strategy | V1 Required | `docs/security/rate-limits.md` plus relevant module docs | OTP, QR redeem, order submit, login, payment/correction, and table display fetch limits. |
| 12 | App wireframes | V1 Required | `docs/apps/{app}/wireframes.md` | Low-fidelity screen structure for primary pages, drawers, dialogs, panels, and empty/error states. |
| 13 | Real UI copy | V1 Required | `docs/apps/{app}/copy.md` plus shared tone rules in `docs/apps/_shared/copy-style.md` | Customer/admin/staff-facing text for critical states without leaking internal/security jargon. |
| 14 | Component breakdown | V1 Lean | `docs/apps/{app}/components.md` | App-level component tree and state ownership. Keep it implementation-guiding, not a full design-system catalog. |
| 15 | Accessibility and responsive rules | V1 Required | Shared baseline in `docs/apps/_shared/accessibility-responsive.md`; app-specific notes only when needed | Mobile-first behavior, touch targets, keyboard/focus, contrast, dynamic content, and no-overlap rules. |
| 16 | App API usage maps | V1 Required | `docs/apps/{app}/api-usage.md` | Which module commands/queries each app calls and which data it may only read. |
| 17 | Test strategy | V1 Required | `docs/testing/strategy.md`, `docs/apps/{app}/test-plan.md`, module-owned test notes | E2E happy paths, branch tests, integration tests, unit tests, idempotency/concurrency tests. |
| 18 | Analytics and audit split | V1 Lean | App analytics in `docs/apps/{app}/analytics.md`; audit in `docs/modules/governance/audit.md` | Minimal product events for v1 and strict audit/domain events. Avoid a full BI plan now. |
| 19 | Logging and observability | V1 Required | `docs/ops/observability.md` plus `docs/modules/governance/reliable-side-effects.md` | Structured logs, correlation IDs, safe metadata, outbox failure visibility, and no secret leakage. |
| 20 | Configuration and environment | V1 Required | `docs/ops/configuration.md` | Required env vars, local/dev/prod differences, secrets, database URL, SMS adapter config, app hosts. |
| 21 | Deployment and runtime operations | V1 Lean | `docs/ops/deployment.md` | Minimal monolith deployment assumptions, startup order, migration order, health checks. |
| 22 | ADRs for locked architectural choices | V1 Lean | `docs/adr/` | Only record hard-to-reverse decisions such as modular monolith, six-app semantic source, QR/session model, and outbox boundary. |

## V2 Backlog

| Item | Where To Document Later | Reason For Deferral |
| --- | --- | --- |
| Detailed product analytics funnels and dashboards | `docs/analytics/` or app analytics docs | V1 needs correctness and audit first; rich analytics can follow real usage. |
| Full design token system and component library | `docs/design/` | V1 needs app-level component breakdown, not a standalone design-system project. |
| Fiscal/e-Adisyon/receipt integrations | `docs/modules/settlement/` and `docs/modules/governance/reliable-side-effects.md` | Out of v1 product scope; requires provider/legal decisions. |
| Printer/KDS/cash drawer/payment terminal contracts | Relevant module folders plus `docs/ops/hardware.md` | Hardware integrations are explicitly out of v1. |
| Visual floor-plan editor | `docs/apps/tenant/` and `docs/modules/tenant-setup/venue-layout.md` | V1 uses ordered hall grids. |
| Inventory/recipe/stock integration | Future tenant setup or inventory context | Common in POS products, but outside v1 QR ordering scope. |
| Rich reporting workspace | `docs/apps/cashier/` or future reporting app | V1 has current business-day payment history only. |
| Performance/load model | `docs/ops/performance.md` | Useful after API/schema shape is known. |

## V3 Backlog

| Item | Where To Document Later | Reason For Deferral |
| --- | --- | --- |
| Multi-location tenants | Platform, Tenant Setup, Access, Settlement | Current v1 tenant equals one restaurant/location. |
| Offline-first POS | Broad app/module/database docs | Major architecture change; not compatible with current v1 assumptions. |
| Device fleet management, firmware, health logs | Future device context | V1 treats ESP32 as table display surface, not inventory. |
| External marketplace/channel orders | Ordering and Settlement | V1 is dine-in QR only. |
| Advanced BI/data warehouse | Future analytics/ops docs | Needs stable production events and reporting needs. |
| Enterprise support roles and delegated platform operators | Platform and Access | PlatformApp is single-user in v1. |

## Do Not Document Now

| Item | Reason |
| --- | --- |
| Microservice deployment topology | The project is a modular monolith; documenting service topology now would contradict the architecture. |
| Kubernetes/service mesh/Helm strategy | Operational overengineering before a running monolith exists. |
| Distributed saga framework | V1 needs transaction boundaries and an outbox, not distributed orchestration. |
| Full event-sourcing model | Current architecture uses domain records, audit, and reliable side effects; event sourcing is not a product requirement. |
| GraphQL schema | No product/API decision requires GraphQL now. |
| Exhaustive future integration contracts | Provider-specific fiscal/payment/hardware contracts should wait until those features enter scope. |

## Execution Rule

Work must follow the order above unless a later task exposes a gap in an earlier layer. If that happens, update the earlier semantic source first, then continue.

Do not create app-level documents that redefine module-owned models. Do not create module-level documents that invent user behavior not present in app docs.
