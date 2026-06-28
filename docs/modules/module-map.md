# Module Map

IoTables is a modular monolith. Apps are user-facing surfaces; modules are domain capability owners.

Apps call module interfaces. Modules own data, rules, state transitions, safety constraints, and future service boundaries.

## Modules

| Module | Purpose | Primary Apps |
| --- | --- | --- |
| Platform / Tenant Registry | Own tenant identity, lifecycle, domain, and platform-level tenant metadata | PlatformApp, TenantApp, CustomerApp, staff apps |
| Identity and Access | Own users, roles, login, first password setup, app permissions, and tenant scoping | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp |
| OTP / Messaging | Own OTP creation, delivery, verification, and provider integration | PlatformApp, TenantApp, CashierApp |
| Sector Starter Templates | Own one-time sector-based starter data application | PlatformApp, TenantApp |
| Venue Layout | Own halls, tables, table state, and table-to-device/display context | TenantApp, CustomerApp, CashierApp, ServiceStaffApp |
| Staff Access | Own staff roles, station assignments, service hall assignments, and app-level staff permissions | TenantApp, CashierApp, StationStaffApp, ServiceStaffApp |
| Menu Catalog | Own categories, products/services, prices, availability, modifiers/options, and station assignment | TenantApp, CustomerApp, CashierApp |
| Table Access / QR | Own table access tokens, ESP32 display QR flow, token redemption, and fresh table presence | CustomerApp |
| Customer Ordering | Own customer carts, order submission, orders, order items, idempotency, and order-to-station routing | CustomerApp, CashierApp, StationStaffApp, ServiceStaffApp |
| Table Session and Billing | Own active table sessions, bill totals, paid amount, remaining balance, and session closure rules | CustomerApp, CashierApp |
| Preparation | Own station queues and preparation state transitions | StationStaffApp, CashierApp, CustomerApp |
| Service Delivery | Own ready-item pickup/delivery transitions and customer delivery state | ServiceStaffApp, CustomerApp, CashierApp |
| Payments | Own payment records, partial/full payments, payment method rules, and payment idempotency | CashierApp, CustomerApp read-only |
| Audit | Own audit events for platform, tenant setup, staff actions, payment, correction, and operational transitions | All admin/staff apps |

## App to Module Usage

| App | Modules Used |
| --- | --- |
| PlatformApp | Platform / Tenant Registry, Identity and Access, OTP / Messaging, Sector Starter Templates, Audit |
| TenantApp | Platform / Tenant Registry, Identity and Access, Staff Access, Venue Layout, Menu Catalog, Sector Starter Templates, OTP / Messaging, Audit |
| CustomerApp | Platform / Tenant Registry, Venue Layout, Menu Catalog, Table Access / QR, Customer Ordering, Table Session and Billing, Preparation, Service Delivery, Payments read-only |
| CashierApp | Identity and Access, Staff Access, Venue Layout, Customer Ordering, Table Session and Billing, Preparation, Service Delivery, Payments, Audit |
| StationStaffApp | Identity and Access, Staff Access, Venue Layout, Menu Catalog read-only, Customer Ordering, Preparation, Audit |
| ServiceStaffApp | Identity and Access, Staff Access, Venue Layout, Customer Ordering, Preparation, Service Delivery, Audit |

## Cross-Cutting Rules

- Every tenant-scoped module must resolve tenant context from trusted server-side routing or authenticated session context.
- Apps must not write directly into another module's owned data.
- Frontend state is never an authority for prices, table session IDs, station IDs, permissions, totals, or order state.
- Critical commands must be guarded, idempotent, transactional where possible, and backed by database constraints.
- One-time operations must record durable completion and must not run on restart, deployment, migration, or release upgrade.
- External side effects such as OTP, payment provider calls, DNS, and device communication need explicit retry and recovery rules.

## Initial Dependency Direction

```text
Apps
  -> Module public interfaces
    -> Module-owned data and rules
```

Modules may publish events for other modules, but direct cross-module table writes should be avoided.

Preferred rule:

```text
Query across module boundaries through public read interfaces.
Mutate across module boundaries through commands or events.
```

## Open Questions

- Which modules get detailed documentation first?
- Should Payments support external providers in v1 or only manual cash/card records?
- Which audit events are mandatory for v1?
