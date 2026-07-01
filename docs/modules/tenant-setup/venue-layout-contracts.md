# Module Contracts: Venue Layout

Source module: [venue-layout.md](venue-layout.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `venue_layout.create_hall` | TenantApp, Provisioning | tenantId, name, displayOrder | Tenant Admin/Provisioning; unique hall name/order in tenant | Insert hall; audit for TenantApp changes | Hall |
| `venue_layout.update_hall` | TenantApp | hallId, editable fields | Tenant Admin own tenant; cannot cross tenant | Update hall; audit | Updated hall |
| `venue_layout.disable_hall` | TenantApp | hallId, reason | Tenant Admin; reject if active tables/sessions make disable unsafe | Set enabled false; do not delete history | Disabled hall |
| `venue_layout.create_table` | TenantApp, Provisioning | tenantId, hallId, name, displayOrder | Tenant Admin/Provisioning; hall belongs to tenant; unique table name/order in hall | Insert table; audit for TenantApp changes | Table |
| `venue_layout.update_table` | TenantApp | tableId, hall/order/name/enabled fields | Tenant Admin; table belongs to tenant; moving hall preserves runtime history | Update table; audit | Updated table |
| `venue_layout.disable_table` | TenantApp | tableId, reason | Tenant Admin; reject if active TableSession exists | Set enabled false; do not delete history | Disabled table |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `venue_layout.get_table_context` | CustomerApp, CashierApp, Ordering, Fulfillment | tenantId, tableId | Caller must already satisfy app/session scope | Table label, hall, enabled state |
| `venue_layout.get_hall_table_board` | TenantApp, CashierApp | tenantId | Tenant Admin or Cashier role | Halls, tables, and caller-specific derived table state references; CashierApp may receive operational `CashierTableState` composed from runtime contexts |
| `venue_layout.list_halls` | TenantApp, Staff Access | tenantId | Tenant-scoped actor | Hall list for setup/assignment |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `table_session_billing.get_active_table_session` | Build operational table board without owning runtime state. |
| `customer_ordering.list_table_orders` | Support derived table state where needed. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `venue_layout.changed` | Hall/table setup changes | TenantApp, Staff Access, Audit |
| `table.disabled` | Table is disabled | Table Presence, Table Display Provisioning |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_hall` | Hall name/order conflicts in tenant. |
| `duplicate_table` | Table name/order conflicts in hall. |
| `active_session_blocks_disable` | Table/hall cannot be disabled while active runtime use exists. |
| `not_runtime_owner` | Caller attempted to mutate orders/sessions/payments through Venue Layout. |
