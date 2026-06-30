# CashierApp API Usage

CashierApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login | `POST /api/v1/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Cashier app scope. |
| First password setup | `POST /api/v1/auth/first-password/begin`, `POST /api/v1/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | Cashier requires OTP proof. |
| OTP state/send/verify | `/api/v1/auth/otp-challenges/{challengeId}...` | [OTP Messaging](../../modules/access/otp-messaging-api.md) | Used only during protected setup flows. |
| Session check/logout | `GET /api/v1/auth/session`, `POST /api/v1/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Human staff session. |
| Venue board | `GET /api/v1/cashier/venue/board` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Operational table overview. |
| Active table session | `GET /api/v1/cashier/tables/{tableId}/active-session` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Cashier opens table context. |
| Table orders | `GET /api/v1/cashier/table-sessions/{tableSessionId}/orders` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Read all table session orders. |
| Bill summary | `GET /api/v1/cashier/table-sessions/{tableSessionId}/bill-summary` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Server-calculated total/paid/remaining. |
| Check detail | `GET /api/v1/cashier/checks/{checkId}` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Check/adisyon state. |
| Check payments | `GET /api/v1/cashier/checks/{checkId}/payments`, `POST /api/v1/cashier/checks/{checkId}/payments` | [Payments](../../modules/settlement/payments-api.md) | Record payment requires `Idempotency-Key`. |
| Payment history | `GET /api/v1/cashier/payments` | [Payments](../../modules/settlement/payments-api.md) | Current business-day operational history. |
| Void payment | `POST /api/v1/cashier/payments/{paymentId}/void` | [Payments](../../modules/settlement/payments-api.md) | Requires reason and `Idempotency-Key`. |
| Corrections | `GET /api/v1/cashier/checks/{checkId}/corrections`, `POST /api/v1/cashier/checks/{checkId}/corrections` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Mutation requires reason and `Idempotency-Key`. |
| Close session | `POST /api/v1/cashier/table-sessions/{tableSessionId}/close` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Requires zero remaining balance. |
| Preparation state | `GET /api/v1/cashier/order-items/{orderItemId}/preparation` | [Preparation](../../modules/fulfillment/preparation-api.md) | Read-only operational visibility. |
| Delivery state | `GET /api/v1/cashier/order-items/{orderItemId}/delivery` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Read-only operational visibility. |
| Operational audit | `GET /api/v1/cashier/audit-events` | [Audit](../../modules/governance/audit-api.md) | Payment/correction/closure evidence. |

## Explicit Non-Usage

CashierApp does not configure tenant setup, create tenants, prepare station items, deliver service items, or submit customer orders.
