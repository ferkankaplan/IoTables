# CashierApp UI States
### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, OTP required, OTP expired |
| Cashier Workspace | loading, empty active sessions, grouped halls/tables, stale table state |
| Session Detail Panel | loading, no active session, active session, closed session, item exception attention |
| Payment Drawer/Dialog | empty amount, invalid amount, over-remaining amount, submitting, recorded |
| Correction Drawer/Dialog | note, item void, payment void, reason required, target invalid |
| Close Session Dialog | disabled until zero balance, confirming, closing, closed |
| Payment History | loading, empty today, payment voided, actor visible |

### Empty States

- No active sessions: show table board with available tables.
- Session panel for available table: show no active session.
- Payment History empty: show no current business-day payments.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| User lacks cashier role | Block app access |
| OTP required/expired | Continue first-login setup; do not open workspace |
| Payment amount zero/negative | Block submit |
| Payment exceeds remaining balance | Block/reject in v1 |
| Duplicate payment submit | Disable while pending; backend returns original payment |
| Check closed | Block payment/correction |
| Remaining balance above zero | Disable close session |
| Item void target not `pending` or `cannot_prepare` | Block/reject item void |
| Any payment exists on Check | Block/reject item void in v1 |
| Payment already voided | Show voided state |
| Reason missing for correction/void | Block submit and focus reason |
| Stale session state | Refresh panel and require user to retry action |

### Success and Confirmation States

- Payment success updates paid and remaining amounts server-side.
- Full payment enables explicit close action.
- Close success updates table to available.
- Item void success recalculates bill and marks item voided.
- Payment void success recalculates paid/remaining and shows reason.
- Correction note success appends audit-visible note.

### Stale and Retry States

- Multiple cashiers can operate same tenant; every action must handle stale totals.
- Payment and close actions must re-read server-calculated balance.
- Duplicate close returns already-closed result.
- Session detail should refresh after payment/correction/fulfillment changes.

### Visual Priority Rules

- Tables with active sessions must be distinguishable from available tables.
- Tables with `cannot_prepare` items need attention state.
- Remaining balance should be prominent.
- Closed sessions should not look actionable.

### Copy Requirements

- Use Check/Adisyon language for bill settlement.
- Do not expose customer payment, split check, item/person split, fiscal receipt, or external provider controls.
- Correction copy must make clear that every correction requires a reason and audit.
