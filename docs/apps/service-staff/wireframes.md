# ServiceStaffApp Wireframes

ServiceStaffApp wireframes define the service delivery workspace. They describe operational workflow and layout responsibility, not React component APIs, CSS, database ownership, or backend contracts.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../_shared/wireframe-rules.md](../_shared/wireframe-rules.md)
- [../_shared/component-model.md](../_shared/component-model.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Route and Workspace Decisions

ServiceStaffApp lives on the tenant host:

```text
https://[tenant].iotables.net/service
```

| Surface | URL | UI Shape | Purpose |
| --- | --- | --- | --- |
| Service Login | `/service/login` | Durable page | Service staff login and first-password gate. |
| Service Queue | `/service` | Durable workspace | Ready and picked-up items for authorized halls. |
| Item Detail | `/service?item=:orderItemId` | Context panel/drawer | Inspect item detail without leaving queue. |
| Recent Deliveries | `/service?view=recent` | Workspace view | Same-day delivered/recent service activity. |

Route state may select hall filters, item, or recent view, but hall authorization comes from Staff Access and Service Delivery backend guards.

## Login

Login is the only unauthenticated ServiceStaffApp surface.

Required states:

| State | Behavior |
| --- | --- |
| Loading | Keep login shell stable. |
| Invalid credentials | Reject safely. |
| First password change required | Force password change before service access. |
| No service role | Block app access. |
| Tenant unavailable/suspended | Block service access. |

Service staff first-password change does not require OTP in the current release.

## Service Tracking Disabled

When service delivery tracking is disabled, ServiceStaffApp has no active runtime authority.

Required behavior:

- no ready queue appears;
- no pickup/delivered/bulk controls appear;
- state explains that this tenant does not use separate delivery tracking;
- staff is directed back to available staff apps or logout.

Disabled mode must not imply that ServiceStaffApp can enable tracking. TenantApp owns that setting.

## Service Queue

Service Queue is the primary workspace when tracking is enabled.

```text
+------------------------------------------------+
| Service header / workload / filters            |
+------------------------------------------------+
| Table group: Masa 001                          |
| [Ready item] [Picked-up item]                  |
| [Bulk deliver selection bar]                   |
+------------------------------------------------+
| Item detail panel / action drawer              |
+------------------------------------------------+
```

Queue grouping:

- primary grouping: table;
- secondary ordering: oldest ready item first inside each table group;
- filters: hall, table, station, status;
- metrics: ready count, picked-up count, oldest ready age, delivered count today, average ready-to-delivered time when enough data exists.

Item card content:

| Field | Notes |
| --- | --- |
| Hall/table label | Delivery destination and scope. |
| Source station | Where the item came from. |
| Product/service label | Order snapshot label. |
| Quantity | Ordered quantity. |
| Notes | Delivery-relevant notes only. |
| Ready age | Time since station marked ready. |
| Delivery status | ready, picked up, delivered/recent. |

Queue states:

| State | Behavior |
| --- | --- |
| Loading | Keep service header and grouping shell stable. |
| Empty ready queue | Show no ready items for authorized halls. |
| Grouped by table | Table groups stay stable while items update. |
| Stale item | Disable unsafe actions and refresh item. |
| Unauthorized hall | Remove item or reject action safely. |
| Service tracking disabled | Hide delivery controls and show blocked state. |

## Item Detail Panel

Item detail opens without leaving the service queue.

It shows:

- hall/table;
- source station;
- ready time;
- product/service;
- quantity;
- delivery-relevant notes;
- current delivery status;
- allowed action bar.

Allowed actions:

| Current State | Actions |
| --- | --- |
| ready | `Teslim aldım`, `Teslim edildi` |
| picked_up | `Teslim edildi` |
| delivered | Read-only recent state |
| not ready/stale/closed | Read-only blocked state |

Item detail states:

| State | Behavior |
| --- | --- |
| Loading | Keep queue selection visible. |
| Item not found | Show safe missing item state and return to queue. |
| Unauthorized hall | Remove from queue and show safe message. |
| Already delivered | Show delivered read-only state. |
| Service tracking disabled | Hide mutation controls. |

## Bulk Delivery

Bulk delivery is available only for selected ready/picked-up items on the same table.

Rules:

- selection cannot span multiple tables;
- selected items must be ready or picked up;
- submit uses one idempotency key;
- backend validates every selected item;
- failure is all-or-nothing;
- duplicate replay shows original bulk result.

States:

| State | Behavior |
| --- | --- |
| Selecting | Same-table selection bar appears. |
| Invalid mixed-table selection | Block action and explain same-table rule. |
| Submitting | Disable selection and delivery controls. |
| Delivered | Remove delivered items from active queue and show result. |
| Stale item in selection | Reject whole bulk action and refresh selection. |
| Duplicate replay | Show original delivered result. |

## Recent Deliveries

Recent Deliveries shows same-day delivered/recent service activity.

States:

| State | Behavior |
| --- | --- |
| Same-day recent deliveries | Show delivered items with table, item, time, and actor when visible. |
| No recent deliveries | Show no same-day deliveries. |
| Loading | Keep service context stable. |

Recent view is read-only. It must not expose payment, cashier correction, tenant setup, station preparation, or customer session controls.

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Touch table groups; item detail and bulk review use full-height drawers. |
| Tablet | Table groups plus detail drawer. |
| Desktop | Queue workspace with detail panel and selection bar. |

No layout may depend on viewport-width font scaling. Table labels, station names, item names, notes, and bulk action labels must wrap without overlapping controls.

## Accessibility

- Login, queue filters, item detail, pickup, delivery, and bulk delivery must work by keyboard.
- Same-table selection must be announced and visible.
- Bulk mixed-table error must be text, not color alone.
- Status labels must have accessible text.
- Drawers/dialogs must trap and restore focus.
- Queue updates must not move focus unexpectedly.

## Data Visibility Boundaries

ServiceStaffApp may show only fields allowed by [visibility.md](visibility.md).

Never show:

- tenant setup edit controls;
- station preparation mutation controls;
- cashier-only notes;
- payment data;
- bill or balance summary;
- close-session controls;
- customer identity/session/cart data;
- raw internal IDs as authority;
- stack traces or provider payloads.

## Current Release Out-of-Scope UI

The following UI must not appear in ServiceStaffApp the current release:

- create/edit halls, tables, stations, products, prices, categories, staff, or tenant settings;
- create customer order;
- start/ready/cannot-prepare station actions;
- receive payment;
- close table session;
- discount/refund/cancel item as financial correction;
- tenant service-tracking setting toggle;
- cashier correction controls.

## Acceptance Check

This wireframe package is valid when:

- every ServiceStaffApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- service tracking disabled blocks all delivery mutation controls;
- hall scope is visible but not trusted to frontend state;
- bulk delivery is same-table, all-or-nothing, and idempotent;
- single-item transitions are duplicate-safe;
- no forbidden current release control appears.
