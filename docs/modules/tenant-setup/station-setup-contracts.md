# Module Contracts: Station Setup

Source module: [station-setup.md](station-setup.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `station_setup.create_station` | TenantApp, Provisioning | tenantId, name, displayOrder | Tenant Admin/Provisioning; unique station name/order | Insert station; audit for TenantApp changes | Station |
| `station_setup.update_station` | TenantApp | stationId, name/order | Tenant Admin own tenant | Update station; audit | Updated station |
| `station_setup.disable_station` | TenantApp | stationId, reason | Tenant Admin; station has no active queue requiring work; enabled products must be disabled/rerouted first | Set enabled false; preserve history | Disabled station |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `station_setup.list_stations` | TenantApp, Menu Catalog, Staff Access | tenantId, includeDisabled flag | Tenant-scoped actor | Station list |
| `station_setup.get_station_context` | StationStaffApp, CashierApp, Preparation | stationId | Caller must satisfy station/tenant scope | Station label and enabled state |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `station.changed` | Station setup changes | Menu Catalog, Staff Access, Preparation, Audit |
| `station.disabled` | Station disabled | Menu Catalog, Preparation guards |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_station` | Name/order conflicts inside tenant. |
| `station_has_orderable_products` | Enabled menu items still route to station. |
| `station_has_active_queue` | Station has pending/preparing work. |
