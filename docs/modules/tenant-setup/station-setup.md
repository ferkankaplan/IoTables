# Module: Station Setup

## Purpose

Station Setup owns tenant fulfillment station definitions such as kitchen, coffee, bar, or service stations.

It defines where products/services may route, but it does not own station queue execution.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Station | Entity | create, update, disable |
| Station lifecycle | State | enabled, disabled |
| Station display order/name | Configuration | manage TenantApp presentation |
| Station setup validation | Rule | prevent unsafe disable when runtime work exists |

## Not Owned

- Product/service definitions and product-to-station assignment, owned by Menu Catalog.
- Station staff assignment, owned by Staff Access.
- Preparation queue items and statuses, owned by Fulfillment / Preparation.
- Service delivery state.
- Payments, billing, or table sessions.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | manage stations | Own tenant |
| Menu Catalog | read active stations for product routing | Read-only |
| StationStaffApp | read authorized station context | Authenticated staff only |
| CashierApp | read station context for order item status | Own tenant |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Manage station | Create/update/disable station | TenantApp |
| List stations | Expose station choices for menu routing and Staff Access assignment | TenantApp, Menu Catalog, Staff Access |
| Get station context | Show operational labels | StationStaffApp, CashierApp |

## Internal Rules

- A station belongs to exactly one tenant.
- Disabled stations cannot receive newly submitted order items.
- Products/services route to exactly one station in the current release.
- Station disable must consider active menu routing and active preparation items.
- Station names are display labels, not trusted identifiers.

## Operational Safety

- Disabling a station with active preparation items must be blocked or require explicit recovery workflow.
- Menu routing must be revalidated after station changes.
- Station setup changes should be audited.
- Station reads by staff must still be constrained by Staff Access assignment.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| Station | active -> disabled | tenant, id, name, displayOrder, enabled | Station belongs to one tenant; disabled stations cannot receive new preparation items; menu products assigned to disabled stations cannot remain orderable | Disable instead of hard-delete when menu assignments, staff assignments, or preparation history reference it |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Station Management workspace |
| StationStaffApp | Reads assigned station labels/context |
| CashierApp | Reads item station context |

## Future Service Boundary

- Own data: station definitions and lifecycle.
- Own APIs: station CRUD, station lookup.
- Published events: station.created, station.updated, station.disabled.
- Consumed events: tenant.suspended.
- Must not leak: preparation queue state into Tenant Setup.

## Open Questions

None currently.
