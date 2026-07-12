# CashierApp Test Plan

This document defines CashierApp-visible test coverage for the current release. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

Source context:

- [definition.md](definition.md)
- [end-to-end.md](end-to-end.md)
- [scenarios.md](scenarios.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [wireframes.md](wireframes.md)
- [copy.md](copy.md)
- [components.md](components.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Test Scope

CashierApp tests prove that cashier staff can log in with first-password setup, monitor active table sessions, inspect a single Check/Adisyon, record partial/full payments, perform only allowed corrections, view current-day payment history, and explicitly close paid sessions.

Out of scope for this test plan:

- tenant setup changes;
- station preparation and service delivery mutation;
- customer order creation;
- customer payment links/pay-at-table;
- split checks, item/person payment split, moved items, fiscal/e-Adisyon/ÖKC issuance;
- external provider settlement;
- arbitrary historical reporting.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| K-01 Cashier First Login | Bootstrap cashier changes password with tenant-GSM OTP. |
| K-02 Monitor and Inspect Active Session | Cashier sees hall/table board, active session, bill summary, orders, payments, and corrections. |
| K-03 Record Partial Payment | Cashier records amount below remaining balance with one idempotency key. |
| K-04 Record Full Payment and Close Session | Remaining balance payment is recorded, then session closes explicitly. |
| K-05 Add Cashier Note Correction | Cashier records reason-required note and audit evidence. |
| K-06 Void Order Item | Eligible pending/cannot-prepare item is voided before any payment exists. |
| K-07 Void Payment | Non-provider payment on open Check is voided with reason. |
| K-08 View Payment History | Current business-day payment records show amount, method, actor, time, and void state. |

## Branch Coverage

### Login, Password Setup, and Access

| Branch | Expected Test Result |
| --- | --- |
| Invalid credentials | Reject safely. |
| Bootstrap password required | Force password change. |
| User lacks cashier role | Block CashierApp. |
| User disabled | Reject access. |
| Tenant unavailable | Block access. |

### Board and Session Visibility

| Branch | Expected Test Result |
| --- | --- |
| No active sessions | Table board shows available tables. |
| Table has active session | Tile shows active state, totals, paid, remaining, latest state. |
| Selected table has no active session | Session panel shows available state. |
| Service tracking disabled | Cashier sees derived final state according to fulfillment visibility. |
| Item cannot_prepare exists | Table/session shows attention state. |
| Session changes while panel open | Stale action is rejected or panel refreshes. |
| Multiple cashiers viewing same session | Totals and action eligibility refresh from server. |

### Payment Recording

| Branch | Expected Test Result |
| --- | --- |
| Empty amount | Block submit. |
| Zero/negative amount | Block/reject. |
| Amount exceeds remaining | Reject in frontend and backend. |
| Duplicate payment same key/request | Original payment result returned. |
| Same idempotency key different request | Conflict returned. |
| Payment during closed Check | Rejected. |
| Concurrent payment changes remaining balance | Backend recomputes and rejects stale overpayment. |
| Mixed payment need | Multiple payment records, no `mixed` method. |

### Corrections and Voids

| Branch | Expected Test Result |
| --- | --- |
| Reason missing | Reject and focus reason. |
| Note on active Check | Correction and audit recorded. |
| Item pending/cannot_prepare and no payment | Item void allowed. |
| Item preparing/ready/picked_up/delivered | Item void rejected. |
| Any payment exists on Check | Item void rejected. |
| Item already voided | Current state returned or stale rejected without duplicate mutation. |
| Payment open and non-provider | Payment void allowed. |
| Payment on closed Check | Payment void rejected. |
| Payment already voided | Current state returned or stale rejected without duplicate mutation. |

### Session Closure

| Branch | Expected Test Result |
| --- | --- |
| Remaining balance above zero | Close disabled/rejected. |
| Remaining balance zero | Close enabled. |
| Close clicked twice | Existing closed state returned or stale command rejected without duplicate closure. |
| Payment recorded concurrently | Balance is recomputed before close. |
| New order races with close | Transaction guards prevent attachment to closed session. |
| Check already closed | No mutation; current closed/stale state shown. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Cashier login and bootstrap password change | Browser/API tests. |
| Cashier first password setup requires OTP | First-password setup tests verify tenant-GSM OTP proof. |
| Cashier sees halls, tables, sessions, latest state, total, paid, remaining | Browser/component/API tests. |
| Session detail opens in context | Browser layout tests. |
| Every active TableSession has one Check/Adisyon | API/domain tests. |
| Payments recorded against Check | API/domain tests. |
| Partial payment does not close session | API/browser tests. |
| Zero balance enables explicit closure only | Browser/API tests. |
| Duplicate payment submit does not duplicate records | Idempotency/concurrency tests. |
| Duplicate close does not duplicate closure | Transaction/unique constraint tests. |
| Only current release allowed corrections available | UI absence and API rejection tests. |
| Payments, voids, corrections, and closures audited | Integration/audit tests. |
| Out-of-scope payment/split/fiscal/provider flows absent | UI absence tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| Login | loading, invalid credentials, first password change required. |
| Cashier Workspace | loading, empty active sessions, grouped halls/tables, stale table state. |
| Session Detail Panel | loading, no active session, active session, closed session, item exception attention. |
| Payment Drawer/Dialog | empty amount, invalid amount, over-remaining amount, submitting, recorded. |
| Correction Drawer/Dialog | note, item void, payment void, reason required, target invalid. |
| Close Session Dialog | disabled until zero balance, confirming, closing, closed. |
| Payment History | loading, empty today, payment voided, actor visible. |

## API Usage Coverage

CashierApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/auth/login-requirements` | First-password requirement discovery. |
| `POST /api/auth/login` | Cashier scope, missing role, invalid credentials. |
| `POST /api/auth/first-password/begin` | Setup token and OTP-required password-change state. |
| `POST /api/auth/first-password/complete` | Password policy and setup-token validation. |
| `GET /api/auth/session` | Protected route access. |
| `POST /api/auth/logout` | Session revocation. |
| `GET /api/cashier/venue/board` | Hall/table board and `CashierTableState`. |
| `GET /api/cashier/tables/{tableId}/active-session` | Empty vs active table session. |
| `GET /api/cashier/table-sessions/{tableSessionId}/orders` | Session order inspection. |
| `GET /api/cashier/table-sessions/{tableSessionId}/bill-summary` | Server-calculated totals. |
| `GET /api/cashier/checks/{checkId}` | Check detail and state. |
| `GET /api/cashier/checks/{checkId}/payments` | Check payment list. |
| `POST /api/cashier/checks/{checkId}/payments` | Payment idempotency, overpayment, closed Check. |
| `GET /api/cashier/payments` | Current business-day payment history. |
| `POST /api/cashier/payments/{paymentId}/void` | Payment void reason, idempotency, closed Check. |
| `GET /api/cashier/checks/{checkId}/corrections` | Correction history. |
| `POST /api/cashier/checks/{checkId}/corrections` | Note, item void, reason, idempotency, blocked target. |
| `POST /api/cashier/table-sessions/{tableSessionId}/close` | Zero-balance close and duplicate close behavior. |
| `GET /api/cashier/order-items/{orderItemId}/preparation` | Cashier-visible preparation state. |
| `GET /api/cashier/order-items/{orderItemId}/delivery` | Cashier-visible delivery state. |
| `GET /api/cashier/audit-events` | Payment/correction/closure evidence. |

## Security and Abuse Coverage

Required tests:

- tenant context is resolved from host/session, not body/query tenant IDs;
- cashier cannot cross tenant hosts;
- user without cashier role cannot access CashierApp;
- unsafe payment, correction, void, close, OTP send/verify, and logout requests require CSRF where applicable;
- payment/correction idempotency keys are scoped to tenant, actor/context, route, and target;
- frontend totals cannot authorize payment or close;
- overpayment, closed Check, stale target, and invalid correction fail closed;
- two concurrent cashiers cannot corrupt payment, correction, or close state;
- item void cannot bypass preparation/payment guards;
- payment void cannot erase original payment data;
- audit records exist for payments, voids, corrections, and closures;
- setup, preparation, service mutation, customer payment, split, provider, and fiscal controls are absent.

## Accessibility and Responsive Coverage

Required checks:

- login, OTP, hall filters, table selection, session panel, payment drawer, correction drawer, payment void, and close dialog work by keyboard;
- dialogs/drawers trap and restore focus;
- money amounts and blocked states are not color-only;
- close disabled and blocked correction reasons are announced;
- touch targets for table tiles and settlement actions are usable;
- mobile drawers and desktop panels avoid overlapping table labels, item names, amounts, reasons, and buttons;
- live board refresh does not steal focus.

## Copy Coverage

Tests must assert that:

- CashierApp uses [copy.md](copy.md) for login, password reset OTP, payment, correction, and close states;
- Password reset OTP copy references the platform-owned tenant identity GSM without exposing full sensitive data;
- `Adisyon`, `Toplam`, `Ödenen`, and `Kalan` labels are used consistently;
- blocked correction/payment/close copy explains the reason;
- duplicate/stale copy tells cashier to refresh/trust current server state;
- setup, split check, customer payment, fiscal, provider, discount, and refund labels are absent.

## Forbidden Control Coverage

CashierApp tests must prove these controls are absent:

- tenant, hall, table, station, product, category, price, staff, or tenant settings editing;
- customer order creation;
- station preparation start/ready/cannot-prepare actions;
- service pickup/deliver actions;
- split check, merge check, moved item, or item/person payment split;
- manual discount, service fee, campaign, tax override, or price edit;
- customer payment link/provider checkout;
- fiscal/e-Adisyon/ÖKC issuance;
- refund after session closure.

## Traceability

When implementation begins:

- browser E2E tests should reference CashierApp scenarios K-01 through K-08;
- API tests should reference [api-usage.md](api-usage.md) and Settlement/Payments contracts;
- payment/correction idempotency tests should reference Payments and Table Session and Billing transaction sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

CashierApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- OTP, money mutation, stale totals, duplicate-submit, and concurrent cashier coverage are defined;
- table board `CashierTableState` is traceable to module/data sources;
- UI state and copy coverage are defined;
- forbidden CashierApp runtime/control leaks are explicitly tested absent;
- semantic index is regenerated after this document changes.
