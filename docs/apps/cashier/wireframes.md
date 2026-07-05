# CashierApp Wireframes

CashierApp wireframes define the cashier settlement workspace. They describe operational workflow and layout responsibility, not React component APIs, CSS, database ownership, or backend contracts.

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

CashierApp lives on the tenant host:

```text
https://[tenant].iotables.net/cashier
```

| Surface | URL | UI Shape | Purpose |
| --- | --- | --- | --- |
| Cashier Login | `/cashier/login` | Durable page | Cashier login, first-password change, and OTP verification. |
| Cashier Workspace | `/cashier` | Durable workspace | Hall/table board, active sessions, balances, and latest state. |
| Session Detail | `/cashier?session=:sessionId` | Context panel/drawer | Inspect and settle one active TableSession without leaving the board. |
| Payment History | `/cashier/payments` | Durable page | Current business-day payment review. |

The workspace is the primary surface. Table/session details, payment entry, correction, payment void, and close-session flows open as contextual panels, drawers, or dialogs.

## Login and First Password Setup

Login is the only unauthenticated CashierApp surface.

Required states:

| State | Behavior |
| --- | --- |
| Loading | Keep login shell stable. |
| Invalid credentials | Reject without revealing tenant or user details. |
| First password change required | Force password change before workspace access. |
| OTP required | Send/verify OTP through tenant GSM for cashier bootstrap. |
| OTP expired/locked | Keep cashier inside setup flow and require safe retry. |
| No cashier role | Block app access. |
| Tenant unavailable/suspended | Block access. |

Cashier first-password setup requires OTP in the current release. Station and service staff OTP behavior must not be copied into this flow.

## Cashier Workspace

Cashier Workspace is a dense operational board.

```text
+--------------------------------------------------------+
| Cashier header / tenant / session status / refresh     |
+----------------------+---------------------------------+
| Hall tabs / filters   | Session detail panel            |
| Table board           | Orders / Check / Payments       |
| Active table tiles    | Payment / Correction / Close    |
+----------------------+---------------------------------+
```

Workspace content:

| Region | Responsibility |
| --- | --- |
| Header | Tenant label, cashier actor, refresh/logout, stale indicator. |
| Hall tabs/filter | Switch hall context without changing cashier authorization. |
| Table board | Tables grouped by hall with active/empty/attention state. |
| Session panel | Active TableSession, Check/Adisyon, orders, payments, corrections. |
| Action drawers/dialogs | Payment, correction, payment void, close session. |

Table tile content:

| Field | Notes |
| --- | --- |
| Hall/table label | Human-readable location. |
| Active session state | Empty, active, closing/closed, stale. |
| Total/paid/remaining | Server-calculated summary only. |
| Latest order/fulfillment state | Operational status and attention flags. |
| Cannot-prepare flag | Prominent cashier attention state. |

The board may show operational `TableState`, but Venue Layout does not own runtime financial/order state. Runtime values are derived from Settlement, Ordering, Fulfillment, and Payments.

## Session Detail Panel

Session detail opens without leaving the table board.

It shows:

- table and hall label;
- TableSession status and opened time;
- single current release Check/Adisyon;
- orders and order items with price snapshots;
- preparation and delivery state where relevant;
- payments and void state;
- cashier corrections and notes;
- server-calculated total, paid, and remaining.

Allowed actions:

| Current State | Actions |
| --- | --- |
| Active check, remaining > 0 | Record payment, allowed corrections. |
| Active check, remaining = 0 | Close session, allowed corrections that remain legal. |
| Closed check/session | Read-only except explicit recovery outside normal current release flow. |
| Stale panel | Refresh before mutation. |

## Payment Drawer

Payment entry is a drawer/dialog launched from the session panel.

Required fields:

| Field | Behavior |
| --- | --- |
| Amount | Positive amount, cannot exceed current remaining balance. |
| Method | `cash`, `card`, or `transfer`. |
| Optional note | Safe cashier note only. |

Rules:

- payment submit uses one `Idempotency-Key`;
- frontend disables duplicate submit while pending;
- backend recomputes remaining balance and rejects overpayment;
- mixed payment is multiple payment records, not a `mixed` method;
- payment success updates bill summary from server response.

## Close Session Dialog

Close session is explicit.

States:

| State | Behavior |
| --- | --- |
| Remaining > 0 | Close action disabled. |
| Remaining = 0 | Close action enabled. |
| Confirming | Show table/check being closed. |
| Closing | Disable close and settlement mutations. |
| Already closed | Show current closed state without duplicate closure. |
| Stale balance | Refresh summary and require retry. |

Zero balance must not silently close the TableSession.

## Correction Drawer

Correction drawer supports only current release allowed corrections.

| Correction | Availability |
| --- | --- |
| Internal cashier note | Active Check/Adisyon only. |
| Item void | Item is `pending` or `cannot_prepare` and no payment exists on the Check. |
| Payment void | Non-provider payment on open Check. |

Every correction requires reason, idempotency, target revalidation, and audit. The drawer must not expose manual discounts, service fees, manual order items, price edits, refunds after closure, split checks, or item/person settlement.

## Payment History

Payment History is a current business-day operational review page.

It shows:

- payment method;
- amount and currency;
- table/check/session reference;
- cashier actor;
- recorded time;
- void state and reason when visible.

Historical arbitrary reporting is out of the current release unless a reporting workspace is introduced.

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Hall switcher, table list, session/payment/correction drawers full-height. |
| Tablet | Table board with sliding session drawer. |
| Desktop | Board and persistent session panel with modal confirmations. |

No layout may depend on viewport-width font scaling. Table labels, money amounts, item names, reasons, and action labels must wrap without overlapping controls.

## Accessibility

- Login, OTP, board filters, table selection, payment, correction, void, and close flows must work by keyboard.
- Dialogs/drawers must trap and restore focus.
- Money amounts must include accessible text, not color alone.
- Disabled close and blocked correction reasons must be announced as text.
- Live board updates must not move focus unexpectedly.

## Data Visibility Boundaries

CashierApp may show only fields allowed by [visibility.md](visibility.md).

Never show:

- Platform tenant controls;
- TenantApp setup mutation controls;
- station preparation mutation controls;
- service delivery mutation controls;
- customer cart/session internals;
- customer payment link/pay-at-table controls;
- fiscal/e-Adisyon/ÖKC issuance controls;
- raw internal IDs as authority;
- stack traces or provider payloads.

## Current Release Out-of-Scope UI

The following UI must not appear in CashierApp the current release:

- create/edit tenant, halls, tables, stations, products, prices, categories, or staff;
- create customer order;
- prepare, mark ready, cannot-prepare, pick-up, or deliver station/service items;
- split checks, merge checks, move items between checks, or item/person split payment;
- manual discounts, service fees, campaign adjustments, tax overrides, or price edits;
- customer payment links or external provider checkout;
- fiscal receipt/e-Adisyon/ÖKC issuance;
- refunds after session closure.

## Acceptance Check

This wireframe package is valid when:

- every CashierApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- the table board keeps context while settlement actions run;
- money totals are server-calculated and never frontend-authoritative;
- payment/correction idempotency and duplicate-submit protection are visible;
- close session is explicit and zero-balance-gated;
- no forbidden current release control appears.
