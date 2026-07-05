# CashierApp Components

This document maps CashierApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

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

- Components own cashier settlement workflow responsibilities, not tenant setup, station preparation, service delivery mutation, or customer ordering.
- Components preserve table board context while opening session, payment, correction, and close surfaces.
- Components must represent stale totals, duplicate-submit, pending, invalid amount, blocked correction, and closed-session states.
- Components must not trust frontend-calculated totals or frontend-selected tenant/table IDs as authority.
- Components must not expose forbidden current release controls.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `CashierShell` | Cashier route frame, session gate, tenant/cashier context. | Session check, tenant route |
| `CashierLogin` | Login, first-password change, OTP setup. | Identity and Access, OTP Messaging |
| `CashierWorkspace` | Hall/table board and selected session workspace. | Venue Layout, Settlement |
| `CashierHeader` | Tenant label, actor, refresh, stale and logout controls. | Session, venue board |
| `HallTableBoard` | Halls and table tiles with operational state. | Venue Layout `CashierTableState` |
| `CashierTableTile` | Empty/active/attention/closed/stale table state. | Venue board, bill summary |
| `SessionDetailPanel` | Orders, Check/Adisyon, payments, corrections, totals. | Settlement, Ordering, Payments, Fulfillment |
| `OrderItemStatusList` | Cashier-visible order item and fulfillment states. | Ordering, Preparation, Service Delivery |
| `BillSummaryPanel` | Server-calculated total, paid, remaining, close eligibility. | Table Session and Billing |
| `PaymentDrawer` | Amount/method/note entry and payment submit state. | Payments |
| `CorrectionDrawer` | Note, item void, payment void, reason and target validation. | Table Session and Billing, Payments |
| `CloseSessionDialog` | Explicit zero-balance close confirmation and stale handling. | Table Session and Billing |
| `PaymentHistoryView` | Current business-day payment list. | Payments |
| `CashierStateMessage` | Loading, empty, blocked, stale, retry, and forbidden states. | UI states, copy |

## Shell and Access Components

`CashierShell` owns:

- cashier route frame;
- protected session check;
- tenant host context;
- cashier actor context;
- refresh and logout.

`CashierLogin` owns:

- cashier login;
- first-password change;
- OTP send/verify flow through tenant GSM;
- invalid credential state;
- no-role state.

Cashier login must not skip OTP for bootstrap password setup.

## Board Components

`CashierWorkspace` owns:

- venue board loading/empty states;
- hall grouping;
- selected table/session route state;
- stale board refresh;
- session panel placement.

`HallTableBoard` displays caller-specific `CashierTableState`. It may render active session, latest operational state, total, paid, remaining, and attention flags, but it must not become the source of truth for runtime state.

`CashierTableTile` displays:

- hall/table label;
- empty or active state;
- active session reference;
- total/paid/remaining summary;
- latest order/fulfillment state;
- cannot-prepare attention;
- stale/closed marker.

Tile click opens `SessionDetailPanel`; it must not mutate session/payment state directly.

## Session Components

`SessionDetailPanel` owns:

- selected TableSession identity;
- Check/Adisyon state;
- order list;
- payment list;
- correction history;
- current server-calculated bill summary;
- action entry points.

`OrderItemStatusList` owns cashier-visible item state only. It may show preparation and delivery status, but it must not show station/service mutation actions.

`BillSummaryPanel` owns:

- total amount;
- paid amount;
- remaining amount;
- payment count;
- correction indicators;
- close eligibility.

Close eligibility must come from server-calculated remaining balance and current session/check state.

## Payment Components

`PaymentDrawer` owns:

- amount input;
- method selection: cash, card, transfer;
- optional safe note;
- disabled pending submit;
- one idempotency key per submit attempt;
- server response handling for updated paid/remaining.

Payment drawer must reject empty, zero/negative, and over-remaining amount before submit, but backend rejection remains authoritative.

## Correction Components

`CorrectionDrawer` owns allowed current release correction choices:

| Correction | Component Behavior |
| --- | --- |
| Internal note | Requires reason and active Check. |
| Item void | Requires eligible item and no payment on Check. |
| Payment void | Requires non-provider payment on open Check. |

Correction behavior:

- reason required;
- disable submit while pending;
- use one idempotency key per submit attempt;
- refresh target state on stale or blocked response;
- show audit-oriented success state.

The component must not expose unrestricted order editing, price editing, discounting, refunds, split checks, or session moves.

## Close Session Components

`CloseSessionDialog` owns:

- zero-balance gate;
- confirmation copy;
- pending close state;
- already-closed state;
- stale balance refresh.

Close-session does not require `Idempotency-Key` in the current release. The component still disables duplicate clicks and accepts already-closed/current-state responses without creating a new closure.

## Payment History Components

`PaymentHistoryView` owns current business-day payment review.

It may show:

- method;
- amount;
- table/check reference;
- cashier actor;
- recorded time;
- void state and reason.

It must not become an arbitrary reporting workspace in the current release.

## State Components

Use `CashierStateMessage` for:

- loading;
- invalid credentials;
- OTP required/expired/locked;
- no cashier role;
- no active sessions;
- no active session for selected table;
- stale board/session;
- payment over remaining;
- duplicate payment replay;
- reason required;
- blocked correction;
- already closed session;
- current-day payment history empty.

State messages must use [copy.md](copy.md).

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Tenant scope | Host/session decides tenant; frontend cannot choose tenant. |
| Table board | Venue Layout composes derived state; runtime state remains owned by Settlement/Ordering/Fulfillment/Payments. |
| Totals | Server-calculated only. |
| Payment | Idempotent command with backend overpayment guard. |
| Correction | Narrow current release types only, reason-required, idempotent, audited. |
| Close session | Explicit, zero-balance, backend-recomputed state. |
| Customer/payment provider/fiscal | No current release controls. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects CashierApp visibility;
- payment/correction/close flows preserve table board context;
- duplicate-submit and stale-state handling are represented;
- server-calculated totals are visually and behaviorally authoritative;
- forbidden current release controls cannot be reached from any component.
