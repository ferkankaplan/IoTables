# Module Map

IoTables is a modular monolith.

Apps are user-facing surfaces. Bounded contexts are the primary architectural units. Internal modules are implementation and documentation units inside those contexts.

The goal is encapsulation: apps call context/module interfaces; internal data, rules, state transitions, and safety constraints stay behind the owning boundary.

App documents in [docs/apps](../apps/README.md) define cross-app behavior, happy paths, branches, UI states, and acceptance criteria. Module, schema, and API decisions must implement those flows instead of inventing independent product semantics.

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
| Platform | Platform tenant lifecycle, provisioning, sector starter application, tenant availability resolution | PlatformApp, TenantApp allowed profile update, tenant apps read | Platform-only decisions; tenant runtime must not leak in as direct mutation |
| Access | Human accounts, roles, app access, login sessions, OTP/TOTP | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | Security boundary; CustomerOrderingSession is not a human identity |
| Tenant Setup | Tenant-operational configuration: venue, menu/catalog, table display provisioning | TenantApp, CustomerApp read, staff/cashier read | Configuration source for runtime contexts; staff permissions remain in Access |
| Ordering | Customer physical presence, anonymous customer session, cart, order submission, order records, Settlement session/check command usage | CustomerApp, CashierApp read, staff read | The core customer-order lifecycle |
| Fulfillment | Preparation and service delivery state after order submission | StationStaffApp, ServiceStaffApp, CustomerApp read, CashierApp read | Operational execution of accepted order items |
| Settlement | Billing summary, payments, cashier corrections, table session closure | CashierApp, CustomerApp read-only | Financial/runtime settlement boundary |
| Governance | Audit, policy evidence, and reliable external side-effect records | All admin/staff apps | Cross-cutting record of critical actions and non-transactional effect execution state |

## Context Folder Map

| Context | Folder | Primary Contract |
| --- | --- | --- |
| Platform | [platform](platform/README.md) | tenant lifecycle and provisioning |
| Access | [access](access/README.md) | human identity, app access, staff authorization, OTP/TOTP |
| Tenant Setup | [tenant-setup](tenant-setup/README.md) | tenant-owned operational configuration |
| Ordering | [ordering](ordering/README.md) | customer presence, cart, order submission |
| Fulfillment | [fulfillment](fulfillment/README.md) | preparation and delivery execution |
| Settlement | [settlement](settlement/README.md) | billing, payments, corrections, session closure |
| Governance | [governance](governance/README.md) | audit, policy evidence, reliable external side effects |

## Internal Modules

### Platform

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Tenant Registry | [platform/tenant-registry.md](platform/tenant-registry.md) | Tenant identity, subdomain, GSM, lifecycle status | Provisioning, PlatformApp, TenantApp allowed profile update, tenant runtime resolution |
| Provisioning | [platform/provisioning.md](platform/provisioning.md) | Tenant creation orchestration and recovery state | PlatformApp |
| Sector Starter Templates | [platform/sector-starter-templates.md](platform/sector-starter-templates.md) | One-time sector starter records and template application proof | Provisioning, PlatformApp options, TenantApp read |

### Access

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Identity | [access/identity-access.md](access/identity-access.md) | Users, credentials, sessions, platform owner bootstrap, TOTP | All authenticated apps |
| Staff Authorization | [access/staff-access.md](access/staff-access.md) | Staff profiles, roles, station assignments, hall assignments | TenantApp, staff/cashier apps |
| OTP Messaging | [access/otp-messaging.md](access/otp-messaging.md) | OTP challenges, verification, delivery attempts | TenantApp, CashierApp, Identity |

### Tenant Setup

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Venue Layout | [tenant-setup/venue-layout.md](tenant-setup/venue-layout.md) | Halls, tables, ordered table grid, table state lookup | TenantApp, CustomerApp, CashierApp, ServiceStaffApp |
| Station Setup | [tenant-setup/station-setup.md](tenant-setup/station-setup.md) | Fulfillment station definitions and lifecycle | TenantApp, Menu Catalog, Staff Access, staff/cashier apps |
| Menu Catalog | [tenant-setup/menu-catalog.md](tenant-setup/menu-catalog.md) | Categories, products/services, variants/portions, modifiers, prices, availability overrides, product-to-station routing | TenantApp, CustomerApp, Ordering |
| Table Display Provisioning | [tenant-setup/table-display-provisioning.md](tenant-setup/table-display-provisioning.md) | Table display claims and credentials for ESP32 QR screens | TenantApp, Ordering |
| Tenant Operational Settings | [tenant-setup/tenant-operational-settings.md](tenant-setup/tenant-operational-settings.md) | Public display name and service delivery tracking mode | TenantApp, Fulfillment read, public tenant context |

### Ordering

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Table Presence | [ordering/table-presence.md](ordering/table-presence.md) | TableAccessToken redemption and fresh table presence | CustomerApp, Customer Ordering |
| Customer Session and Cart | [ordering/customer-ordering.md](ordering/customer-ordering.md) | CustomerOrderingSession, active customer cart, cart validation | CustomerApp |
| Order Submission | [ordering/customer-ordering.md](ordering/customer-ordering.md) | Order transaction, order items, idempotency, product/variant/price/modifier snapshots | CustomerApp, CashierApp read |

### Fulfillment

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Preparation | [fulfillment/preparation.md](fulfillment/preparation.md) | Station queues and `pending -> preparing -> ready` transitions | StationStaffApp, CustomerApp read, CashierApp read |
| Service Delivery | [fulfillment/service-delivery.md](fulfillment/service-delivery.md) | `picked_up` and `delivered` states after preparation readiness | ServiceStaffApp, CustomerApp read, CashierApp read |

### Settlement

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Table Session and Billing | [settlement/table-session-billing.md](settlement/table-session-billing.md) | TableSession, single v1 Check/Adisyon, bill totals, remaining balance, close-session eligibility | CustomerApp read, CashierApp, Ordering command |
| Payments | [settlement/payments.md](settlement/payments.md) | Manual payment records, payment idempotency, non-provider payment void | CashierApp, CustomerApp read |
| Corrections | [settlement/table-session-billing.md](settlement/table-session-billing.md), [settlement/payments.md](settlement/payments.md), [governance/audit.md](governance/audit.md) | Narrow v1 cashier correction workflows with reason and audit | CashierApp |

### Governance

| Internal Module | Doc | Owns | Public Consumers |
| --- | --- | --- | --- |
| Audit | [governance/audit.md](governance/audit.md) | Append-only critical action records | PlatformApp, TenantApp, CashierApp, staff apps |
| Reliable Side Effects | [governance/reliable-side-effects.md](governance/reliable-side-effects.md) | Outbox records and external effect attempts for non-transactional integrations | Modules that emit SMS, printer, fiscal, payment-provider, DNS, or device side effects |

## App to Context Usage

| App | Contexts Used |
| --- | --- |
| PlatformApp | Platform, Access, Governance |
| TenantApp | Platform profile read/update, Access, Tenant Setup, Governance |
| CustomerApp | Platform read, Tenant Setup read, Ordering, Fulfillment read, Settlement read-only |
| CashierApp | Platform read, Access, Tenant Setup read, Ordering read, Fulfillment read, Settlement, Governance |
| StationStaffApp | Platform read, Access, Tenant Setup read, Ordering read, Fulfillment, Governance |
| ServiceStaffApp | Platform read, Access, Tenant Setup read, Ordering read, Fulfillment, Governance |

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
- External side effects such as OTP, DNS, table display communication, printer calls, fiscal calls, payment providers, and notifications need explicit retry and recovery rules. New side effects must use Reliable Side Effects unless their owning module records an equivalent durable attempt log.
- Mutable operational aggregates must have an explicit concurrency strategy: transaction locks for server-owned transitions, version checks for client-driven updates, or both.

## Architecture Review Findings

### Resolved by This Map

| Finding | Risk | Decision |
| --- | --- | --- |
| Too many top-level modules | The architecture looked fragmented despite a clear six-app product surface | Promote bounded contexts and treat current modules as internal modules |
| Flat module file tree | Documentation still looked like every small topic was a top-level module | Organize module docs by context folder |
| OTP / Messaging was top-level | Security plumbing looked like a business domain | Move it under Access while keeping provider integration isolated |
| Preparation and Service Delivery were separate top-level modules | Operational workflow was split too early | Group both under Fulfillment |
| Table Session, Billing, Payments, and Corrections were scattered | Cashier settlement risked cross-module leakage | Group them under Settlement |
| Audit was listed beside business modules | Audit could become a noisy utility without policy ownership | Move it under Governance |
| Station setup ownership was implicit | TenantApp manages stations but no module clearly owned station lifecycle | Add Tenant Setup / Station Setup as station definition owner |
| Table Access / QR mixed two owners | Provisioning is tenant setup; fresh presence is ordering security | Split into Table Display Provisioning and Table Presence; keep [shared QR flow](_shared/table-access-qr-flow.md) as cross-module explanation |
| Product/service station routing was open | Menu and fulfillment ownership would change if one product routed to many stations | V1 keeps exactly one station per product/service |
| Tenant lifecycle status was open | Provisioning and runtime availability needed exact states | V1 uses `provisioning`, `active`, `suspended`, `provisioning_failed` |
| Correction workflows were broad | Cashier corrections could become history rewrite | V1 allows only cashier note, pending/cannot_prepare item void before payment, and non-provider payment void on open Check |
| Mandatory audit events were vague | Critical commands needed consistent event names | V1 mandatory event list is defined in [governance/audit.md](governance/audit.md) and [data-model.md](../data-model.md) |
| Staff assignment ownership overlapped Tenant Setup and Access | Schema/API ownership would split station and hall permissions across contexts | Staff roles, station assignments, and hall assignments belong to Access / Staff Access; Tenant Setup owns only the referenced halls/stations |
| Availability/sold-out model was too minimal | Live menus need temporary sold-out without disabling catalog history | Menu Catalog owns `AvailabilityOverride` for temporary product/variant orderability |
| Variant/portion pricing was not modeled | Size/portion pricing is common in cafes/restaurants | Menu Catalog owns `ProductVariant`; every orderable product has at least one variant |
| Event/outbox strategy was not locked | Future printers, fiscal integrations, payment providers, and notifications need reliable side effects | Governance owns Reliable Side Effects; external integrations need outbox/attempt tracking before implementation |

## Open Questions

None currently.
