# Module Map

IoTables is a modular monolith.

Apps are user-facing surfaces. Bounded contexts are the primary architectural units. Internal modules are implementation and documentation units inside those contexts.

The goal is encapsulation: apps call context/module interfaces; internal data, rules, state transitions, and safety constraints stay behind the owning boundary.

App-flow documents in [docs/app-flows](../app-flows/README.md) define cross-app behavior, happy paths, branches, UI states, and acceptance criteria. Module, schema, and API decisions must implement those flows instead of inventing independent product semantics.

## External Reference Findings

These references are not copied as architecture. They are evidence used to avoid an over-fragmented local design.

| Reference | Relevant Pattern | IoTables Decision |
| --- | --- | --- |
| [Square Orders API](https://developer.squareup.com/docs/orders-api/what-it-does) | Orders group line items, totals, payment confirmation, fulfillment progress, and catalog/inventory effects around the order lifecycle | Keep order lifecycle concepts under a cohesive Ordering context instead of scattering every state into top-level modules |
| [Square Catalog API](https://developer.squareup.com/docs/catalog-api/what-it-does) | Catalog owns the seller item library separately from Orders | Keep Menu Catalog inside Tenant Setup, with Ordering reading validated catalog data |
| [Toast Orders API](https://doc.toasttab.com/doc/devguide/portalOrdersApiOverview.html) | Order/check pricing and payment updates are order lifecycle concerns; platform-side pricing is authoritative | Keep backend-calculated pricing, price snapshots, and cashier payments as authoritative server-side flows |
| [Shopify Packwerk](https://shopify.engineering/enforcing-modularity-rails-apps-packwerk) | A large monolith can stay coherent when packages enforce boundaries | Treat bounded contexts as packages with explicit public interfaces |
| [Shopify monolith/component ownership](https://shopify.engineering/shopify-monolith) | Explicit ownership lets large monolith areas evolve without whole-codebase confusion | Give every context one owner and keep cross-context writes behind commands/events |

## Bounded Contexts

| Context | Owns | Primary Apps | Notes |
| --- | --- | --- | --- |
| Platform | Platform tenant lifecycle, provisioning, sector starter application | PlatformApp, TenantApp read | Platform-only decisions; tenant runtime must not leak in as direct mutation |
| Access | Human accounts, roles, app access, login sessions, OTP/TOTP | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | Security boundary; CustomerOrderingSession is not a human identity |
| Tenant Setup | Tenant-operational configuration: venue, staff assignment, menu/catalog, table display provisioning | TenantApp, CustomerApp read, staff/cashier read | Configuration source for runtime contexts |
| Ordering | Customer physical presence, anonymous customer session, cart, order submission, order records, Settlement session/check command usage | CustomerApp, CashierApp read, staff read | The core customer-order lifecycle |
| Fulfillment | Preparation and service delivery state after order submission | StationStaffApp, ServiceStaffApp, CustomerApp read, CashierApp read | Operational execution of accepted order items |
| Settlement | Billing summary, payments, cashier corrections, table session closure | CashierApp, CustomerApp read-only | Financial/runtime settlement boundary |
| Governance | Audit and policy evidence | All admin/staff apps | Cross-cutting record of critical actions |

## Internal Modules

### Platform

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Tenant Registry | `platform-tenant-registry.md` | Tenant identity, subdomain, GSM, lifecycle status | PlatformApp, tenant runtime resolution |
| Provisioning | `platform-tenant-registry.md`, `sector-starter-templates.md` | Tenant creation transaction and recovery state | PlatformApp |
| Sector Starter Templates | `sector-starter-templates.md` | One-time sector starter records and template application proof | PlatformApp, TenantApp read |

### Access

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Identity | `identity-access.md` | Users, credentials, sessions, platform owner bootstrap, TOTP | All authenticated apps |
| Staff Authorization | `staff-access.md` | Staff roles, station assignments, hall assignments | TenantApp, staff/cashier apps |
| OTP Messaging | `otp-messaging.md` | OTP challenges, verification, delivery attempts | TenantApp, CashierApp, Identity |

### Tenant Setup

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Venue Layout | `venue-layout.md` | Halls, tables, ordered table grid, table state lookup | TenantApp, CustomerApp, CashierApp, ServiceStaffApp |
| Menu Catalog | `menu-catalog.md` | Categories, products/services, modifiers, prices, availability, station assignment | TenantApp, CustomerApp, Ordering |
| Staff Directory | `staff-access.md` | Staff profile lifecycle as tenant-owned setup data | TenantApp, Access |
| Table Display Provisioning | `table-access-qr.md` | Table display claims and credentials for ESP32 QR screens | TenantApp, Ordering |

### Ordering

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Table Presence | `table-access-qr.md` | TableAccessToken redemption and fresh table presence | CustomerApp |
| Customer Session and Cart | `customer-ordering.md` | CustomerOrderingSession, active customer cart, cart validation | CustomerApp |
| Order Submission | `customer-ordering.md` | Order transaction, order items, idempotency, price/modifier snapshots | CustomerApp, CashierApp read |

### Fulfillment

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Preparation | `preparation.md` | Station queues and `pending -> preparing -> ready` transitions | StationStaffApp, CustomerApp read, CashierApp read |
| Service Delivery | `service-delivery.md` | `picked_up` and `delivered` states after preparation readiness | ServiceStaffApp, CustomerApp read, CashierApp read |

### Settlement

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Table Session and Billing | `table-session-billing.md` | TableSession, single v1 Check/Adisyon, bill totals, remaining balance, close-session eligibility | CustomerApp read, CashierApp, Ordering command |
| Payments | `payments.md` | Manual payment records, payment idempotency, non-provider payment void | CashierApp, CustomerApp read |
| Corrections | `payments.md`, `table-session-billing.md`, `audit.md` | Narrow v1 cashier correction workflows with reason and audit | CashierApp |

### Governance

| Internal Module | Existing Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Audit | `audit.md` | Append-only critical action records | PlatformApp, TenantApp, CashierApp, staff apps |

## App to Context Usage

| App | Contexts Used |
| --- | --- |
| PlatformApp | Platform, Access, Governance |
| TenantApp | Platform read, Access, Tenant Setup, Governance |
| CustomerApp | Tenant Setup read, Ordering, Fulfillment read, Settlement read-only |
| CashierApp | Access, Tenant Setup read, Ordering read, Fulfillment read, Settlement, Governance |
| StationStaffApp | Access, Tenant Setup read, Ordering read, Fulfillment, Governance |
| ServiceStaffApp | Access, Tenant Setup read, Ordering read, Fulfillment, Governance |

## Dependency Direction

```text
Apps
  -> Context public interfaces
    -> Internal module public interfaces
      -> Module-owned data and rules
```

Allowed dependency direction:

```text
Platform
Access
Tenant Setup
Ordering
Fulfillment
Settlement
Governance
```

Rules:

- Apps must not write directly into another context's owned data.
- Internal modules may query another context only through public read interfaces.
- Cross-context mutation must use commands or events.
- One context must own each aggregate.
- A child module must not expose another child module's tables as its own API.
- Context names are stable architecture; internal module names may evolve while preserving ownership.
- Order submission may call Settlement's public `open session/check if needed` command inside the order transaction; Ordering still does not own TableSession or Check.

## Cross-Cutting Rules

- Every tenant-scoped context must resolve tenant context from trusted server-side routing or authenticated session context.
- Frontend state is never an authority for prices, table session IDs, station IDs, permissions, totals, or order state.
- Critical commands must be guarded, idempotent, transactional where possible, and backed by database constraints.
- One-time operations must record durable completion and must not run on restart, deployment, migration, or release upgrade.
- External side effects such as OTP, DNS, and table display communication need explicit retry and recovery rules.
- Mutable operational aggregates must have an explicit concurrency strategy: transaction locks for server-owned transitions, version checks for client-driven updates, or both.

## Architecture Review Findings

Detailed execution order is tracked in [v1-architecture-backlog.md](../v1-architecture-backlog.md).

### Resolved by This Map

| Finding | Risk | Decision |
| --- | --- | --- |
| Too many top-level modules | The architecture looked fragmented despite a clear six-app product surface | Promote bounded contexts and treat current modules as internal modules |
| OTP / Messaging was top-level | Security plumbing looked like a business domain | Move it under Access while keeping provider integration isolated |
| Preparation and Service Delivery were separate top-level modules | Operational workflow was split too early | Group both under Fulfillment |
| Table Session, Billing, Payments, and Corrections were scattered | Cashier settlement risked cross-module leakage | Group them under Settlement |
| Audit was listed beside business modules | Audit could become a noisy utility without policy ownership | Move it under Governance |
| Product/service station routing was open | Menu and fulfillment ownership would change if one product routed to many stations | V1 keeps exactly one station per product/service |
| Tenant lifecycle status was open | Provisioning and runtime availability needed exact states | V1 uses `provisioning`, `active`, `suspended`, `provisioning_failed` |
| Correction workflows were broad | Cashier corrections could become history rewrite | V1 allows only cashier note, pending/cannot_prepare item void before payment, and non-provider payment void on open Check |
| Mandatory audit events were vague | Critical commands needed consistent event names | V1 mandatory event list is defined in `audit.md` and `data-model.md` |

### Still Needs Follow-Up

| Finding | Why It Matters | Recommended Direction |
| --- | --- | --- |
| Table Access / QR is still one document | Provisioning is tenant setup; fresh presence is ordering security | The ownership is split in the doc; implementation should use separate packages/modules before code starts |
| Availability/sold-out model is still minimal | Live menus need temporary sold-out without disabling catalog history | Add `AvailabilityOverride` before first live menu implementation |
| Variant/portion pricing is not modeled yet | Size/portion pricing is common in cafes/restaurants | Add `ProductVariant` if first tenant needs priced sizes or portions |
| Event/outbox strategy is not locked | Future printers, fiscal integrations, and notifications need reliable side effects | Keep in-process domain events for pure v1 flows; add persistent outbox before external side effects beyond OTP |

## Open Questions

None currently. Remaining sequencing and future follow-ups are tracked in [v1-architecture-backlog.md](../v1-architecture-backlog.md).
