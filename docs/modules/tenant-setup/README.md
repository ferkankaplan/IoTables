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
| [tenant-operational-settings.md](tenant-operational-settings.md) | Public display name and service delivery tracking mode |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [venue-layout-contracts.md](venue-layout-contracts.md) | Hall/table setup and table context contracts |
| [station-setup-contracts.md](station-setup-contracts.md) | Station setup and station context contracts |
| [menu-catalog-contracts.md](menu-catalog-contracts.md) | Menu management, orderability, validation, pricing, and routing contracts |
| [table-display-provisioning-contracts.md](table-display-provisioning-contracts.md) | ESP32 display claim, credential, authentication, and revoke contracts |
| [tenant-operational-settings-contracts.md](tenant-operational-settings-contracts.md) | Public display and service tracking setting contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [venue-layout-api.md](venue-layout-api.md) | Hall, table, and table board endpoints |
| [station-setup-api.md](station-setup-api.md) | Station setup and station context endpoints |
| [menu-catalog-api.md](menu-catalog-api.md) | Customer menu and tenant menu setup endpoints |
| [table-display-provisioning-api.md](table-display-provisioning-api.md) | ESP32 display claim, credential, revoke, rotate, and state endpoints |
| [tenant-operational-settings-api.md](tenant-operational-settings-api.md) | Tenant operational settings endpoints |

## Primary Apps

- TenantApp
- CustomerApp read
- CashierApp read
- StationStaffApp read
- ServiceStaffApp read

## Boundary Rule

Tenant Setup owns configuration. Runtime records such as orders, preparation items, delivery states, table sessions, and payments live outside this context.
