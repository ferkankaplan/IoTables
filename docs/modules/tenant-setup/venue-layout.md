# Module: Venue Layout

## Purpose

Venue Layout owns tenant physical layout: halls, tables, table state, and table context used by QR, ordering, cashier, and service workflows.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Hall | Entity | create, update, disable |
| Table | Entity | create, update, reorder, disable |
| Table operational state | State/read model | empty, active, unavailable where needed |

## Not Owned

- Table display claims and credentials, owned by Table Display Provisioning.
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
| CashierApp | read halls/tables and operational state | Own tenant |
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
- Tables are managed in Hall Management, not a separate primary page in v1.
- V1 uses an ordered table grid inside each hall, not a visual coordinate-based floor plan.
- Disabled tables cannot accept new customer ordering.
- Table identifiers should be tenant-scoped and human readable.
- Table layout changes must not corrupt active TableSessions.

## Operational Safety

- Disabling a table with an active TableSession must require explicit rules.
- Table deletion should be avoided when historical orders/sessions exist; prefer disable.
- Table state used by ordering must be rechecked server-side.
- Hall/table changes should be audited.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Hall | active -> disabled | tenant, id, name, displayOrder, enabled | Hall belongs to one tenant; display order is tenant-local; disabled halls cannot accept normal active use | Disable instead of hard-delete when tables, sessions, orders, or staff hall assignments reference it |
| Table | active -> disabled | tenant, id, hall, name, displayOrder, enabled | Table belongs to exactly one hall; only one active TableSession per tenant/table is allowed by Settlement; v1 uses ordered grid, not visual coordinates | Disable instead of hard-delete when sessions/orders/display credentials exist |
| TableState | derived/read-only | table, active session state, latest order/fulfillment/balance summary | Derived from runtime contexts; Venue Layout must not own session/order/payment state | Rebuildable read model; no independent deletion semantics |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Manage halls/tables with contextual panels |
| CustomerApp | Resolve table context after QR |
| CashierApp | Display table/session board |
| ServiceStaffApp | Locate delivery destination |

## Future Service Boundary

- Own data: halls, tables, ordered table-grid metadata.
- Own APIs: hall/table CRUD, table context lookup.
- Published events: table.disabled, hall.updated.
- Consumed events: table_session.opened, table_session.closed.
- Must not leak: table mutation authority to CustomerApp.

## Open Questions

None currently.
