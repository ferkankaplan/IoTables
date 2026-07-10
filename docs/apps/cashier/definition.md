# CashierApp

## Purpose

CashierApp is the tenant-scoped cashier console for tracking active table sessions, inspecting customer orders, receiving payments, and closing sessions.

It is served from the tenant subdomain:

```text
https://[tenant].iotables.net
```

CashierApp is not a tenant setup interface. It does not manage halls, tables, stations, products, or tenant settings. It operates on the live restaurant state created by customer orders and tenant configuration.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Cashier | Own tenant only | View active tables/sessions, inspect orders, receive partial or full payments, close paid sessions, perform allowed corrections | Cannot configure tenant setup or prepare station items |

The initial cashier user is created automatically by PlatformApp during tenant provisioning when the selected sector starter template includes a cashier staff user. For the initial `cafe` template, the cashier username is `kasiyer` and the temporary password is `admin`.

The cashier must change the temporary password on first login. First-password setup does not require OTP in the current release; later password reset flows use OTP sent to the platform-owned tenant identity GSM. After creation, the cashier is a normal tenant-owned staff user.

## App Authority

CashierApp can operate tenant runtime records related to table sessions and payments.

| Area | Authority |
| --- | --- |
| Active table view | Read physical halls, tables, and table states; reveal virtual test tables only through a temporary page-local toggle |
| Table session view | Read active session details for each table |
| Single check/adisyon view | Read the single current release check/adisyon attached to the table session |
| Order inspection | Read orders and order items attached to a session |
| Payment collection | Create partial or full payment records |
| Balance tracking | Display total, paid, and remaining balance |
| Session closure | Close a session when settlement rules are satisfied |
| Operational correction | Apply explicitly allowed corrections with reason and audit trail |

CashierApp must always be tenant-scoped. Every action belongs to the current tenant resolved from the subdomain.

## Not Authorized

- It does not create or suspend tenants.
- It does not edit tenant identity or tenant setup data.
- It does not create halls, tables, stations, products, or menu categories.
- It does not prepare station tickets.
- It does not create customer QR access tokens for physical tables.
- It may request a fresh QR preview only for `virtual_test` tables when the temporary virtual-table view is explicitly enabled.
- It does not directly mutate station fulfillment state unless a specific correction workflow allows it.
- It does not create customer payment links or pay-at-table flows in the current release.
- It does not issue fiscal/e-Adisyon/ÖKC receipts or external fiscal documents in the current release.
- It does not split checks, merge checks, move items between checks, or perform item/person-based split payment in the current release.

## UX Principle

CashierApp should be a dense operational workspace with minimal page navigation.

The cashier should keep the table/session context while acting. The main screen should show halls, tables, active sessions, balances, and order/payment state. Selecting a table should open a session detail panel. Payment, correction, and close-session flows should appear as drawers or dialogs without losing the table board context.

## Screens and URLs

| Screen | URL | Purpose |
| --- | --- | --- |
| Cashier Login | `https://[tenant].iotables.net/cashier/login` | Authenticate cashier staff |
| Cashier Workspace | `https://[tenant].iotables.net/cashier` | Monitor tables, active sessions, orders, and payments |
| Session Detail Panel | `https://[tenant].iotables.net/cashier?session=:sessionId` | Deep-link to a session while staying in the cashier workspace |
| Payment History | `https://[tenant].iotables.net/cashier/payments` | Review cashier-visible payment records |

Table and session details should open inside the cashier workspace. A separate full page should exist only for durable history or reporting views.

## Core Workflows

### Cashier Login

1. Cashier opens `https://[tenant].iotables.net/cashier/login`.
2. CashierApp authenticates against the current tenant.
3. If the cashier is using the temporary bootstrap password, CashierApp forces password change.
4. CashierApp opens the cashier workspace after successful login and password change.

### Monitor Active Sessions

1. Cashier opens the cashier workspace.
2. CashierApp shows halls and physical tables with current runtime state.
3. Tables with active sessions show total balance, paid amount, remaining balance, and latest order state.
4. Cashier selects a table to inspect the active session in a contextual panel.

Table sessions are created by customer ordering, not by CashierApp. The first customer order on a table opens the session.

Virtual test tables are hidden from the normal cashier board. The cashier may enable a page-local "show virtual tables" control for testing; this state must reset when the page reloads. Only then may the cashier open a virtual table detail panel and display a fresh QR preview for that virtual table.

### Inspect Session

1. Cashier selects a table with an active session.
2. CashierApp opens the session detail panel.
3. CashierApp shows session orders, order items, station status where relevant, payments, and remaining balance.
4. Cashier can start a payment or correction flow from the same panel.

### Single Check / Adisyon

In v1, every active TableSession has exactly one operational Check/Adisyon.

The Check/Adisyon is the cashier-facing bill for the table visit. It groups all submitted orders, order items, price snapshots, payments, and remaining balance for the active TableSession.

The current release does not support:

- multiple checks under the same TableSession;
- split checks;
- merging checks;
- moving items between checks;
- item/person-based payment splitting;
- customer-initiated payment;
- fiscal/e-Adisyon/ÖKC receipt issuance.

Partial payments are still allowed, but they are amount-based payments against the single Check/Adisyon.

### Receive Partial Payment

1. Cashier opens the session detail panel.
2. Cashier enters the amount received.
3. CashierApp validates that the amount is allowed by the payment rules.
4. CashierApp records the payment.
5. CashierApp updates paid amount and remaining balance.
6. Session remains open while remaining balance is greater than zero.

Partial payments reduce the outstanding balance but do not close the session.

### Receive Full Payment and Close Session

1. Cashier opens the session detail panel.
2. Cashier receives the remaining balance.
3. CashierApp records the payment.
4. If remaining balance becomes zero, CashierApp enables session closure.
5. Cashier explicitly closes the session.
6. The table becomes available for a future session.

Session closure is an explicit cashier action. A zero balance alone does not silently close the session unless the product later defines an automatic close policy.

### Correct Session

1. Cashier opens the session detail panel.
2. Cashier chooses an allowed correction action.
3. CashierApp requires a reason.
4. CashierApp applies the correction through a controlled workflow.
5. CashierApp records an audit event.

Correction actions must be narrowly defined before implementation. They must not become an unrestricted way to rewrite order history.

### V1 Correction Rules

Allowed CashierApp corrections in the current release:

- add an internal cashier note to the active TableSession;
- cancel/void an order item only while its preparation state is `pending` or `cannot_prepare` and before any payment has been recorded for the Check/Adisyon;
- void a payment on an open Check/Adisyon when no external payment provider is involved.

Not allowed in the current release:

- manual order items;
- manual discounts;
- service fees;
- refunds after session closure;
- cancellation of items already in `preparing`, `ready`, `picked_up`, or `delivered` state;
- changing item price snapshots directly;
- moving items between checks or sessions.

All current release correction actions are cashier-authorized, reason-required, idempotent, and audited. Tenant Admin approval is not part of the current release correction flow. Broader override workflows must be introduced explicitly later instead of extending cashier correction silently.

Payment History shows the current business day by default. Historical reporting across arbitrary date ranges is out of the current release unless a reporting workspace is introduced.

More than one cashier may operate the same tenant at the same time. CashierApp must rely on backend transactions, row/version checks, idempotency keys, and actor-specific audit records instead of assuming a single active cashier.

## Data Concepts Visible in CashierApp

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Summary | Tenant identity resolved from subdomain |
| Hall | Read | Used to group tables |
| Table | Read | Shows current operational state |
| Table session | Full runtime view | Active operational/billing session for a table |
| Check/Adisyon | Full runtime view | Single current release bill attached to the active TableSession |
| Order | Read | Customer order attached to the session |
| Order item | Read | Includes item status and price snapshot |
| Payment | Create/read | Partial and full payment records |
| Balance | Full runtime view | Total, paid, and remaining amount |
| Correction | Create/read | Narrow current release correction records with reason and actor |
| Session audit | Read | Shows cashier-visible corrections and closure events |

## Operational Safety

CashierApp handles money and live sessions, so all cashier actions must be safe under retries, duplicate clicks, and concurrent requests.

- Payment creation must be idempotent.
- Session closure must be idempotent.
- Current release payment methods are `cash`, `card`, and `transfer`.
- Mixed payment is recorded as multiple payment records against the same Check/Adisyon.
- Current release payment splitting is amount-based only; splitting by item/person is out of scope.
- External payment providers are out of scope for the current release.
- Fiscal/e-Adisyon/ÖKC receipt issuance is out of scope for the current release.
- Payment and balance updates must run inside a transaction.
- Balance must be calculated server-side from order item price snapshots, corrections, and payment records.
- A payment request must not create duplicate payment records when submitted more than once.
- A session must not close while remaining balance is greater than zero unless an explicit approved settlement rule exists.
- A closed session must not accept new orders, payments, or corrections except through an explicit recovery workflow.
- Every correction must include a reason and audit event.
- If an external payment provider is introduced later, payment provider calls need explicit retry, rollback, and reconciliation rules.

## Integration Expectations

| Context / Module | Expected Use |
| --- | --- |
| Platform / Tenant Registry | Resolve tenant availability from subdomain |
| Access / Identity and Access | Cashier authentication |
| Access / Staff Access | Cashier role enforcement |
| Tenant Setup / Venue Layout | Read halls and tables |
| Tenant Setup / Station Setup | Read station labels and context |
| Ordering / Customer Ordering | Read orders and order items |
| Fulfillment / Preparation | Read station/order item preparation state |
| Fulfillment / Service Delivery | Read item delivery state |
| Settlement / Table Session and Billing | Read sessions, calculate balances, close sessions |
| Settlement / Payments | Record partial and full payments |
| Governance / Audit | Record payments, corrections, and session closures |

## Security Rules

- CashierApp resolves tenant context from `[tenant].iotables.net`.
- Cashier users can access only their own tenant.
- Cashier routes require authentication.
- Cashier actions require cashier permission.
- Starter cashier password is temporary and must be changed on first login.
- Starter cashier first-password setup requires password change without OTP in the current release.
- Cashier password reset uses OTP sent to the platform-owned tenant identity GSM.
- Payments and corrections must be audited.
- CashierApp must not trust frontend-calculated totals.
- CashierApp must not expose PlatformApp or TenantApp configuration capabilities.

## Open Questions

None currently.
