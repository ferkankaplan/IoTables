# CashierApp Acceptance Criteria
CashierApp is accepted for the current release when:

- cashier must log in and change bootstrap password on first login;
- cashier first password setup does not require OTP in the current release;
- cashier sees halls, tables, active sessions, latest order state, total, paid, and remaining balance;
- session detail opens in context without losing table board;
- every active TableSession has exactly one Check/Adisyon;
- payments are recorded against the Check;
- partial payments reduce remaining balance but do not close the session;
- zero balance enables explicit closure but does not silently close;
- duplicate payment submit does not create duplicate payment records;
- duplicate close request is idempotent;
- only current release allowed corrections are available;
- all payments, voids, corrections, and closures are audited;
- CustomerApp payment, split check, item/person split, fiscal receipt, and external provider flows are absent.
