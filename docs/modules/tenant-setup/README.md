# Tenant Setup Context

Tenant Setup owns tenant-operational configuration used by runtime apps.

It is the source for halls, tables, stations, menu/catalog, and table display provisioning. Staff permissions may reference halls and stations, but those assignments are owned by Access / Staff Access.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [venue-layout.md](venue-layout.md) | Halls, tables, ordered table grid, table context |
| [station-setup.md](station-setup.md) | Fulfillment station definitions and lifecycle |
| [menu-catalog.md](menu-catalog.md) | Categories, products/services, variants/portions, prices, modifiers, availability overrides, product-to-station routing |
| [table-display-provisioning.md](table-display-provisioning.md) | ESP32 table display claims and credentials |

## Primary Apps

- TenantApp
- CustomerApp read
- CashierApp read
- StationStaffApp read
- ServiceStaffApp read

## Boundary Rule

Tenant Setup owns configuration. Runtime records such as orders, preparation items, delivery states, table sessions, and payments live outside this context.
