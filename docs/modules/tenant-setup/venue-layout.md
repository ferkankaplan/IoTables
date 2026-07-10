# Module: Venue Layout

## Purpose

Venue Layout owns tenant physical layout: halls, tables, table state, and table context used by QR, ordering, cashier, and service workflows.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Hall | Entity | create, update, disable, allocate 100 table-number slots |
| Table | Entity | create as slot, update, reorder, disable, promote eligible virtual slots to physical |
| Table operational state | State/read model | empty, active, unavailable where needed |

## Not Owned

- Table display firmware packages and credentials, owned by Table Display Provisioning.
- TableAccessToken generation.
- TableSession billing lifecycle.
- Customer carts/orders.
- Staff service hall assignment, owned by Staff Access.
- Station/product definitions.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | manage halls and tables | Own tenant |
| CustomerApp | read table context from QR/session | Fresh presence rules apply |
| CashierApp | read physical halls/tables and operational state; optionally reveal virtual test tables for the current page session | Own tenant; virtual test tables are hidden by default |
| ServiceStaffApp | read authorized hall/table context | Hall permissions apply |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Manage hall | Create/update/disable hall | TenantApp |
| Manage table | Create/update/disable table | TenantApp |
| Get table context | Resolve table information | CustomerApp, CashierApp, staff apps |
| Get hall/table board | Operational table view | CashierApp, TenantApp |

## Internal Rules

- Tables belong to halls.
- Tables are managed in Hall Management, not a separate primary page in the current release.
- The current release uses an ordered table grid inside each hall, not a visual coordinate-based floor plan.
- Each hall owns exactly one 100-number table slot range. The first hall uses `100-199`, the second `200-299`, the third `300-399`, and so on.
- Creating a hall creates its 100 table slots in the same transaction.
- Table slots start as `virtual_test` unless explicitly promoted to `physical`.
- `x00` and `x99` slots are permanent virtual test/system boundary slots and must never be promoted to physical tables.
- Virtual test tables are hidden from operational boards by default. CashierApp may reveal them only through a temporary page-local "show virtual tables" control.
- Physical tables may use ESP32 display firmware. Virtual test tables must not receive ESP32 display credentials or firmware packages.
- Disabled tables cannot accept new customer ordering.
- Table identifiers should be tenant-scoped and human readable.
- Table layout changes must not corrupt active TableSessions.

## Operational Safety

- Disabling a table with an active TableSession must require explicit rules.
- Table deletion should be avoided when historical orders/sessions exist; prefer disable.
- Hall creation and its 100 table-slot creation must commit atomically; partial slot creation is invalid.
- Promotion from `virtual_test` to `physical` must fail for `x00` and `x99` slots.
- Table state used by ordering must be rechecked server-side.
- Hall/table changes should be audited.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Hall | active -> disabled | tenant, id, name, displayOrder, tableNumberBase, enabled | Hall belongs to one tenant; display order is tenant-local; tableNumberBase allocates one 100-number range; disabled halls cannot accept normal active use | Disable instead of hard-delete when tables, sessions, orders, or staff hall assignments reference it |
| Table | virtual_test -> physical / disabled | tenant, id, hall, tableNumber, name, displayOrder, mode, enabled | Table belongs to exactly one hall; tableNumber must stay inside hall range; `x00` and `x99` are permanent virtual_test slots; only one active TableSession per tenant/table is allowed by Settlement | Disable instead of hard-delete when sessions/orders/display credentials exist |
| TableState | derived/read-only | table, active session state, latest order/fulfillment/balance summary | Derived from runtime contexts; Venue Layout must not own session/order/payment state | Rebuildable read model; no independent deletion semantics |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Manage halls/tables with contextual panels |
| CustomerApp | Resolve table context after QR |
| CashierApp | Display physical table/session board; optionally reveal virtual test tables for temporary QR testing |
| ServiceStaffApp | Locate delivery destination |

## Future Service Boundary

- Own data: halls, tables, ordered table-grid metadata.
- Own APIs: hall/table CRUD, table context lookup.
- Published events: table.disabled, hall.updated.
- Consumed events: table_session.opened, table_session.closed.
- Must not leak: table mutation authority to CustomerApp.

## Open Questions

None currently.
