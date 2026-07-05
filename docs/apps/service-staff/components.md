# ServiceStaffApp Components

This document maps ServiceStaffApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

Source context:

- [definition.md](definition.md)
- [wireframes.md](wireframes.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [../_shared/component-model.md](../_shared/component-model.md)
- [../_shared/wireframe-rules.md](../_shared/wireframe-rules.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)

## Component Ownership Rules

- Components own service delivery workflow responsibilities, not tenant setup, station preparation, cashier, or payment behavior.
- Components preserve queue context while opening item details and bulk review.
- Components must represent disabled tracking, stale, unauthorized, duplicate-safe, pending, and failure states.
- Components must not trust frontend hall/table/item IDs for authorization.
- Components must not expose station preparation mutation controls.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `ServiceStaffShell` | Service route frame, session gate, tenant/hall context. | Session check, tenant route |
| `ServiceLogin` | Login and first-password change without OTP. | Identity and Access |
| `ServiceDisabledState` | Tracking disabled state with no delivery mutation controls. | Tenant Operational Settings via Service Delivery |
| `ServiceQueueWorkspace` | Ready/picked-up queue grouped by table. | Service Delivery |
| `ServiceWorkloadBar` | Ready/picked-up/delivered counters and age metrics. | Service Delivery workload |
| `ServiceTableGroup` | Same-table group with selectable ready/picked-up items. | Service ready items |
| `DeliveryItemCard` | Table, station, product, quantity, note, ready age, status. | Service ready items |
| `DeliveryItemPanel` | Detail view without leaving queue context. | Service Delivery |
| `DeliveryActionBar` | Picked-up and delivered action availability and pending state. | Service Delivery transitions |
| `BulkDeliverySelectionBar` | Same-table selection, review, submit, duplicate replay. | Bulk delivery |
| `RecentDeliveriesView` | Same-day delivered/recent service activity. | Recent deliveries |
| `ServiceStateMessage` | Loading, empty, stale, unauthorized, blocked, retry states. | UI states, copy |

## Shell and Access Components

`ServiceStaffShell` owns:

- service route frame;
- protected session check;
- tenant/service tracking gate;
- authorized hall context;
- logout.

`ServiceLogin` owns:

- service staff login;
- first-password change;
- invalid credential state;
- no-role state.

Service staff first-password flow must not show OTP controls in the current release.

`ServiceDisabledState` owns:

- tracking disabled message;
- no operational queue state;
- no mutation controls;
- route-away/logout action.

## Queue Components

`ServiceQueueWorkspace` owns:

- ready item loading/empty states;
- table grouping;
- oldest-ready sorting inside table groups;
- filters by hall, table, station, and status;
- stale/unauthorized item removal;
- recent deliveries navigation.

`ServiceWorkloadBar` displays:

- ready item count;
- picked-up item count;
- oldest ready item age;
- delivered count today;
- average ready-to-delivered time when available.

`ServiceTableGroup` owns same-table selection state. It must prevent mixed-table bulk submission.

`DeliveryItemCard` displays:

- hall/table label;
- source station;
- item label;
- quantity;
- delivery-relevant note;
- ready age;
- delivery status;
- detail/action entry.

## Item Detail and Actions

`DeliveryItemPanel` owns:

- selected item details;
- current server status;
- delivery-relevant notes;
- read-only delivered/stale/closed states.

`DeliveryActionBar` owns allowed actions:

| Current State | Available Actions |
| --- | --- |
| ready | Pick up, deliver |
| picked_up | Deliver |
| delivered | Read-only recent |
| not ready/stale/closed | Read-only blocked |

Action bar behavior:

- disable all item actions while pending;
- update only after backend acceptance;
- refresh on stale transition failure;
- remove item on unauthorized hall response;
- never expose preparation, payment, or cashier correction actions.

## Bulk Delivery Components

`BulkDeliverySelectionBar` owns:

- selected items for one table;
- invalid mixed-table selection state;
- review count;
- pending bulk submit;
- idempotent duplicate replay result;
- all-or-nothing failure state.

Bulk delivery must use one idempotency key per submit attempt and must not partially deliver selected items.

## Recent Deliveries

`RecentDeliveriesView` owns same-day delivered/recent activity.

It is read-only and may show:

- table label;
- item label;
- source station;
- delivered time;
- actor when visible.

It must not provide payment, cashier correction, preparation, or setup actions.

## State Components

Use `ServiceStateMessage` for:

- loading;
- invalid credentials;
- no service role;
- no hall scope;
- service tracking disabled;
- empty ready queue;
- no recent deliveries;
- stale item;
- unauthorized hall;
- already delivered;
- invalid mixed-table selection;
- bulk stale failure;
- network retry.

State messages must use [copy.md](copy.md).

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Service tracking | Disabled mode hides all mutation controls. |
| Hall scope | Backend revalidates every read and transition. |
| Ready state | Comes from Preparation; Service Delivery does not store ready state. |
| DeliveryState | Stores only picked_up and delivered. |
| Bulk delivery | Same-table, all-or-nothing, idempotent. |
| Recent deliveries | Read-only same-day service activity. |
| Payments/session/cashier | Never visible as mutation controls. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects ServiceStaffApp visibility;
- disabled tracking blocks all service mutation controls;
- single-item transitions have pending/stale behavior;
- bulk delivery same-table and idempotent behavior is represented;
- recent deliveries are read-only;
- forbidden current release controls cannot be reached from any component.
