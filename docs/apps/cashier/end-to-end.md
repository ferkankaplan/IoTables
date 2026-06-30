# CashierApp End-to-End Role

This document extracts the parts of the shared v1 end-to-end flow where this app participates.

See the full shared flow: [../_shared/master-end-to-end.md](../_shared/master-end-to-end.md).

### 9. Cashier Settles and Closes Session
1. Cashier logs into CashierApp.
2. First cashier password setup requires OTP to tenant GSM.
3. Cashier sees halls, tables, active sessions, balances, and latest order state.
4. Cashier opens a table session panel.
5. Cashier receives partial or full payments against the single Check/Adisyon.
6. Payments are amount-based only.
7. Cashier may apply only allowed v1 corrections.
8. When remaining balance is zero, Cashier explicitly closes the TableSession.
9. The table becomes available for a future session.

Acceptance criteria:

- V1 has exactly one Check/Adisyon per TableSession.
- Split checks, merge checks, item/person-based split payment, item move, and customer payment are out of v1.
- Payment creation and session closure are idempotent.
- Session closure is explicit; zero balance alone does not silently close.
- Closed sessions do not accept new orders, payments, or corrections except explicit recovery workflows.

## Allowed Cashier Corrections
V1 allows:

- internal cashier note on active TableSession/Check;
- order item void only while preparation state is `pending` or `cannot_prepare` and before any payment has been recorded for the Check;
- non-provider payment void only on an open Check.

V1 does not allow:

- manual order items;
- manual discounts;
- service fees;
- refunds after session closure;
- cancellation of items already `preparing`, `ready`, `picked_up`, or `delivered`;
- direct price snapshot edits;
- moving items between checks or sessions.

All corrections require cashier permission, reason, idempotency, server-side target validation, and audit.
