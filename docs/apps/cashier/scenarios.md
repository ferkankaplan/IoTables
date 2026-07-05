# CashierApp Scenarios
### K-01: Cashier First Login

Happy path:

1. Cashier opens CashierApp login.
2. Cashier enters bootstrap credentials.
3. Cashier changes password.
4. OTP SMS is sent to tenant GSM.
5. Cashier verifies OTP.
6. Cashier workspace opens.

Branches:

| Branch | Expected Result |
| --- | --- |
| Invalid credentials | Reject |
| OTP expired | Require new OTP |
| OTP verification fails too often | Lock/slow challenge |
| User lacks cashier role | Reject app access |
| User disabled | Reject |

Result:

- Cashier has secure first-login setup.

Ownership:

- CashierApp + Access + OTP/Messaging.

### K-02: Monitor and Inspect Active Session

Happy path:

1. Cashier opens workspace.
2. Cashier sees halls, tables, active session state, latest item state, total, paid, remaining.
3. Cashier selects active table.
4. Session panel opens with orders, items, Check/Adisyon, payments, and corrections.

Branches:

| Branch | Expected Result |
| --- | --- |
| Table has no active session | Show empty/available table state |
| Table session changes while panel open | Panel refreshes or stale action is rejected server-side |
| Service tracking disabled | Fulfillment state uses `ready` as final tracked state |
| Item `cannot_prepare` exists | Highlight cashier attention state |

Result:

- Cashier has operational context without leaving table board.

Ownership:

- CashierApp + Settlement read + Ordering/Fulfillment read.

### K-03: Record Partial Payment

Happy path:

1. Cashier opens active Check.
2. Cashier enters payment amount less than remaining balance.
3. Cashier selects method: `cash`, `card`, or `transfer`.
4. Backend validates amount and idempotency key.
5. Backend records payment against Check.
6. Remaining balance decreases.
7. TableSession remains open.

Branches:

| Branch | Expected Result |
| --- | --- |
| Amount is zero/negative | Reject |
| Amount exceeds remaining balance | Reject in the current release |
| Duplicate submit same key | Return original payment |
| Same key different request | Fail closed |
| Check closed | Reject |
| Cashier lacks permission | Reject |

Result:

- Payment is recorded once and balance is server-calculated.

Ownership:

- CashierApp + Payments + Settlement.

### K-04: Record Full Payment and Close Session

Happy path:

1. Cashier records remaining balance as payment.
2. Remaining balance becomes zero.
3. Cashier explicitly closes TableSession.
4. Backend validates zero balance.
5. Backend closes Check and TableSession in one transaction.
6. Table becomes available for future session.

Branches:

| Branch | Expected Result |
| --- | --- |
| Balance remains above zero | Close is rejected |
| Close clicked twice | Return already closed state idempotently |
| New order arrives during close | Transaction/concurrency control prevents order attaching to closed session |
| Payment recorded concurrently by another cashier | Balance is recalculated server-side before close |
| Check already closed | Return closed state or reject stale command without mutation |

Result:

- Settlement is complete and table can accept a future session.

Ownership:

- CashierApp + Settlement + Payments.

### K-05: Add Cashier Note Correction

Happy path:

1. Cashier opens active session.
2. Cashier adds internal correction note with reason.
3. Backend records CashierCorrection and audit.

Branches:

| Branch | Expected Result |
| --- | --- |
| Reason missing | Reject |
| Session closed | Reject except explicit recovery |
| Duplicate submit | Return original correction by idempotency key |

Result:

- Note is auditable and does not mutate billable records.

Ownership:

- CashierApp + Settlement + Governance.

### K-06: Void Order Item

Happy path:

1. Cashier selects item in `pending` or `cannot_prepare`.
2. Cashier enters reason.
3. Backend verifies no payment has been recorded for the Check.
4. Backend records item void and CashierCorrection.
5. Bill summary recalculates server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| Item is `preparing`, `ready`, `picked_up`, or `delivered` | Reject in the current release |
| Any payment exists on Check | Reject item void in the current release |
| Reason missing | Reject |
| Item already voided | Return current state idempotently or reject stale request |
| Station attempts to void | Not allowed; only CashierApp correction can void |

Result:

- Item is voided through controlled cashier correction.

Ownership:

- CashierApp + Settlement + Ordering read + Preparation read.

### K-07: Void Payment

Happy path:

1. Cashier selects recorded non-provider payment on open Check.
2. Cashier enters reason.
3. Backend records payment void and audit.
4. Bill summary recalculates server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| Payment belongs to closed Check | Reject in the current release |
| Payment already voided | Return current state idempotently or reject stale request |
| External provider payment | Out of the current release; reject if somehow present |
| Reason missing | Reject |

Result:

- Payment no longer counts toward paid amount.

Ownership:

- CashierApp + Payments + Settlement + Governance.

### K-08: View Payment History

Happy path:

1. Cashier opens Payment History.
2. CashierApp shows current business-day payment records visible to the cashier.
3. Cashier can inspect payment method, amount, actor, time, and void state.

Branches:

| Branch | Expected Result |
| --- | --- |
| No payments today | Show empty state |
| Payment was voided | Show void state and reason |
| Cashier requests arbitrary historical report | Out of the current release unless reporting workspace is introduced |
| Tenant has multiple cashiers | Show actor per payment; do not assume single cashier |

Result:

- Payment History supports operational review without becoming a full reporting module.

Ownership:

- CashierApp + Payments + Governance.
