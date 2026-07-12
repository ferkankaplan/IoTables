# StationStaffApp Wireframes

StationStaffApp wireframes define the station preparation workspace. They describe operational workflow and layout responsibility, not React component APIs, CSS, database ownership, or backend contracts.

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

StationStaffApp lives on the tenant host:

```text
https://[tenant].iotables.net/station
```

| Surface | URL | UI Shape | Purpose |
| --- | --- | --- | --- |
| Station Login | `/station/login` | Durable page | Station staff login and first-password gate. |
| Station Selector | `/station/select` | Durable page | Choose one authorized station when staff has multiple. |
| Station Queue | `/station` | Durable workspace | Active preparation queue for selected authorized station. |
| Item Detail | `/station?item=:preparationItemId` | Context panel/drawer | Inspect item detail without leaving queue. |
| Recent Items | `/station?view=recent` | Workspace view | Same-day recent/completed station activity. |

Route state may select station, item, or recent view, but station authority comes from Staff Access and backend Preparation guards.

## Login

Login is the only unauthenticated StationStaffApp surface.

Required states:

| State | Behavior |
| --- | --- |
| Loading | Keep login shell stable. |
| Invalid credentials | Reject safely. |
| First password change required | Force password change before queue access. |
| No station role | Block app access. |
| Tenant unavailable/suspended | Block station access. |

Station staff first-password change requires OTP sent to the platform-owned tenant identity GSM.

## Station Selector

Station Selector appears only when the staff user has more than one authorized station.

States:

| State | Behavior |
| --- | --- |
| Loading | Show authorized station loading state. |
| No authorized stations | Show no station access, not an empty queue. |
| Station disabled | Remove or disable station choice and explain unavailable state. |
| Single station | Skip selector and open queue directly. |

Station labels are operational display labels. The frontend must not treat selected station IDs as authorization proof.

## Station Queue

Station Queue is the primary workspace.

```text
+------------------------------------------------+
| Station header / workload / filters            |
+------------------------------------------------+
| Pending                                         |
| [Item card] [Item card]                         |
| Preparing                                       |
| [Item card]                                     |
| Ready                                           |
| [Item card]                                     |
+------------------------------------------------+
| Item detail panel / action drawer               |
+------------------------------------------------+
```

Queue grouping:

- primary grouping: preparation status;
- secondary ordering: oldest item first inside each group;
- filters: table, order, product/service, status;
- metrics: pending count, preparing count, ready waiting count, oldest pending age, average preparation time when enough data exists.

Item card content:

| Field | Notes |
| --- | --- |
| Table label | Customer/cashier-safe table label. |
| Product/service label | Order snapshot label. |
| Quantity | Ordered quantity. |
| Notes | Preparation-relevant customer/operational notes only. |
| Ordered age | Time since order submission. |
| Status | `pending`, `preparing`, `ready`, `cannot_prepare`. |

Queue states:

| State | Behavior |
| --- | --- |
| Loading | Keep station header and grouping shell stable. |
| Empty queue | Show no active items for selected station. |
| Grouped by status | Status sections stay stable while items update. |
| Stale item | Disable unsafe actions, refresh item, show current state. |
| Unauthorized item removed | Remove from queue or show safe removal state. |
| Station disabled | Remove active station operations. |

## Item Detail Panel

Item detail opens from a queue item without leaving the queue.

It shows:

- table;
- order time;
- product/service;
- quantity;
- variants/modifiers relevant to preparation;
- preparation-relevant note;
- current status;
- transition history when available;
- allowed action bar.

Allowed actions:

| Current State | Actions |
| --- | --- |
| `pending` | `Hazırlamaya başla`, `Hazırlanamıyor` |
| `preparing` | `Hazır`, `Hazırlanamıyor` |
| `ready` | Read-only active/recent state |
| `cannot_prepare` | Read-only exception state |

Item detail states:

| State | Behavior |
| --- | --- |
| Loading | Keep queue selection visible. |
| Item not found | Show safe missing item state and return to queue. |
| Item stale | Refresh before action. |
| Reason required | Focus reason field in cannot-prepare dialog. |
| Closed session / completed item | Show read-only stale state. |

## Preparation Actions

Preparation actions are live state transitions.

| Action | Pending Behavior | Failure Behavior |
| --- | --- | --- |
| Start preparing | Disable item actions; update item only after backend acceptance. | Refresh current state on stale/unauthorized failure. |
| Mark ready | Disable item actions; move item to ready/recent state after backend acceptance. | Reject direct pending-to-ready and show stale/current state. |
| Cannot prepare | Require reason dialog; disable submit while pending. | Keep reason visible and show field/server error. |

Duplicate clicks must not create duplicate transitions. If the backend returns stale transition failure, StationStaffApp refreshes to the current server state.

## Recent / Completed View

Recent view shows same-day station activity that left the active queue or reached a visible terminal/recent state.

States:

| State | Behavior |
| --- | --- |
| Same-day recent items | Show newest recent items with final/recent status and timestamps. |
| No recent items | Show no recent station activity. |
| Loading | Keep station context stable. |

Recent view is read-only. It must not provide cashier correction, payment, delivery, or tenant setup actions.

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Touch queue first; item detail opens as full-height drawer. |
| Tablet | Queue plus item drawer; station selector remains simple. |
| Desktop | Queue groups with persistent detail panel when an item is selected. |

No layout may depend on viewport-width font scaling. Table labels, product names, notes, and action labels must wrap without overlapping action controls.

## Accessibility

- Login, station selection, queue filters, item panels, and preparation actions must work by keyboard.
- Item action buttons need large touch targets.
- Status labels must be text, not color alone.
- Cannot-prepare dialog must focus the reason field when missing.
- Drawer/dialog focus must be trapped and restored.
- Queue updates must not move focus unexpectedly after an action.

## Data Visibility Boundaries

StationStaffApp may show only fields allowed by [visibility.md](visibility.md).

Never show:

- tenant setup edit controls;
- menu price editing;
- cashier-only notes;
- payment data;
- bill or balance summary;
- table session settlement controls;
- customer identity/session/cart data;
- service delivery mutation controls;
- raw internal IDs as authority;
- stack traces or provider payloads.

## Current Release Out-of-Scope UI

The following UI must not appear in StationStaffApp the current release:

- create/edit halls, tables, stations, products, prices, categories, staff, or tenant settings;
- create customer order;
- receive payment;
- close table session;
- discount/refund/cancel item as financial correction;
- mark item delivered to customer;
- reassign product to another station;
- service delivery queue controls;
- cashier correction controls.

## Acceptance Check

This wireframe package is valid when:

- every StationStaffApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- authorized station scope is visible but not trusted to frontend state;
- all live transitions have pending, stale, unauthorized, duplicate-safe, and failure behavior;
- `cannot_prepare` requires a reason and stays operational, not financial;
- no forbidden current release control appears.
