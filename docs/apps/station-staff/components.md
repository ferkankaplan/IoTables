# StationStaffApp Components

This document maps StationStaffApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

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

- Components own station preparation workflow responsibilities, not tenant setup, service delivery, cashier, or payment behavior.
- Components preserve queue context while opening item details and reason dialogs.
- Components must represent stale, unauthorized, duplicate-safe, pending, and failure states for live transitions.
- Components must not trust frontend station IDs for authorization.
- Components must not expose cashier-only notes, payments, bill state, or delivery mutation controls.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `StationStaffShell` | Station app route frame, session gate, tenant/station context. | Session check, tenant route |
| `StationLogin` | Login and first-password change without OTP. | Identity and Access |
| `StationSelector` | Select authorized station when more than one station is assigned. | Staff Access |
| `StationQueueWorkspace` | Active queue grouped by status and sorted oldest first. | Preparation |
| `StationWorkloadBar` | Pending/preparing/ready counts and age metrics. | Preparation workload |
| `PreparationItemCard` | Table, product, quantity, note, elapsed time, status, quick action entry. | Preparation queue |
| `PreparationItemPanel` | Detail view without leaving queue context. | Preparation queue/state |
| `PreparationActionBar` | Start, ready, cannot-prepare action availability and pending state. | Preparation transitions |
| `CannotPrepareDialog` | Reason-required exception flow. | Preparation cannot-prepare |
| `RecentItemsView` | Same-day recent/completed station activity. | Preparation recent items |
| `StationStateMessage` | Loading, empty, stale, unauthorized, blocked, retry states. | UI states, copy |

## Shell and Access Components

`StationStaffShell` owns:

- station route frame;
- protected session check;
- selected station context;
- station access refresh;
- logout.

`StationLogin` owns:

- station staff login;
- first-password change;
- invalid credential state;
- no-role state.

Station staff first-password flow must not show OTP controls in v1.

## Station Selector

`StationSelector` owns:

- authorized station list;
- no authorized stations state;
- disabled station state;
- selected station handoff to queue.

If exactly one station is authorized, the queue opens directly. The selected station remains server-validated on every queue read and transition.

## Queue Components

`StationQueueWorkspace` owns:

- queue loading/empty states;
- status grouping;
- oldest-first sorting;
- filters by table, order, product/service, and status;
- removal of unauthorized/stale items;
- recent view navigation.

`StationWorkloadBar` displays:

- pending item count;
- preparing item count;
- ready waiting count;
- oldest pending age;
- average preparation time when available.

`PreparationItemCard` displays:

- table label;
- item label;
- quantity;
- preparation-relevant note;
- order age;
- status;
- action/detail entry.

## Item Detail and Actions

`PreparationItemPanel` owns:

- selected item details;
- current server status;
- preparation-relevant options/modifiers/notes;
- transition history when available;
- read-only stale/completed states.

`PreparationActionBar` owns allowed transition actions:

| Current State | Available Actions |
| --- | --- |
| `pending` | Start preparing, cannot prepare |
| `preparing` | Mark ready, cannot prepare |
| `ready` | Read-only/recent |
| `cannot_prepare` | Read-only exception |

Action bar behavior:

- disable all item actions while a transition is pending;
- update only after backend acceptance;
- refresh on stale transition failure;
- remove item on unauthorized station response;
- never expose financial correction actions.

`CannotPrepareDialog` owns:

- reason field;
- missing reason validation;
- pending submit;
- stale/unauthorized failure;
- success state.

## Recent Items

`RecentItemsView` owns same-day recent station activity.

It is read-only and may show:

- final/recent status;
- table label;
- item label;
- timestamps;
- exception reason when visible to station staff.

It must not provide payment, cashier correction, delivery, or setup actions.

## State Components

Use `StationStateMessage` for:

- loading;
- invalid credentials;
- no station role;
- no authorized stations;
- station disabled;
- empty queue;
- no recent items;
- stale item;
- unauthorized item removed;
- item not found;
- cannot-prepare reason required;
- network retry.

State messages must use [copy.md](copy.md).

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Station selection | Display only authorized stations; backend revalidates every action. |
| Queue items | Assigned station items only. |
| Notes | Preparation-relevant notes only; no cashier-only notes. |
| Ready state | Station work complete, not customer delivered. |
| Cannot prepare | Operational exception only; no financial mutation. |
| Recent items | Read-only same-day station history. |
| Payments/session/cashier | Never visible as mutation controls. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects StationStaffApp visibility;
- all transitions have pending and stale behavior;
- unauthorized station/item handling is represented;
- `cannot_prepare` requires reason;
- recent items are read-only;
- forbidden v1 controls cannot be reached from any component.
