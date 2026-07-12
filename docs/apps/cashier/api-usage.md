# CashierApp API Usage

CashierApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login requirements | `GET /api/auth/login-requirements` | [Identity and Access](../../modules/access/identity-access-api.md) | Safe first-password requirement discovery. |
| Login | `POST /api/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Cashier app scope. |
| First password setup | `POST /api/auth/first-password/begin`, `POST /api/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | OTP proof required; code is sent to the platform-owned tenant identity GSM. |
| OTP state/send/verify | `/api/auth/otp-challenges/{challengeId}...` | [OTP Messaging](../../modules/access/otp-messaging-api.md) | Used for password reset flows, not current first-password setup. |
| Session check/logout | `GET /api/auth/session`, `POST /api/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Human staff session. |
| Venue board | `GET /api/cashier/venue/board` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Operational physical table overview; optional request-scoped virtual test table reveal. |
| Virtual table QR preview | `POST /api/cashier/virtual-tables/{tableId}/qr-preview` | [Table Presence](../../modules/ordering/table-presence-api.md) | Only for `virtual_test` tables; physical tables use ESP32 display flow. |
| Active table session | `GET /api/cashier/tables/{tableId}/active-session` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Cashier opens table context. |
| Table orders | `GET /api/cashier/table-sessions/{tableSessionId}/orders` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Read all table session orders. |
| Bill summary | `GET /api/cashier/table-sessions/{tableSessionId}/bill-summary` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Server-calculated total/paid/remaining. |
| Check detail | `GET /api/cashier/checks/{checkId}` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Check/adisyon state. |
| Check payments | `GET /api/cashier/checks/{checkId}/payments`, `POST /api/cashier/checks/{checkId}/payments` | [Payments](../../modules/settlement/payments-api.md) | Record payment requires `Idempotency-Key`. |
| Payment history | `GET /api/cashier/payments` | [Payments](../../modules/settlement/payments-api.md) | Current business-day operational history. |
| Void payment | `POST /api/cashier/payments/{paymentId}/void` | [Payments](../../modules/settlement/payments-api.md) | Requires reason and `Idempotency-Key`. |
| Corrections | `GET /api/cashier/checks/{checkId}/corrections`, `POST /api/cashier/checks/{checkId}/corrections` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Mutation requires reason and `Idempotency-Key`. |
| Close session | `POST /api/cashier/table-sessions/{tableSessionId}/close` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Requires zero remaining balance. |
| Preparation state | `GET /api/cashier/order-items/{orderItemId}/preparation` | [Preparation](../../modules/fulfillment/preparation-api.md) | Read-only operational visibility. |
| Delivery state | `GET /api/cashier/order-items/{orderItemId}/delivery` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Read-only operational visibility. |
| Operational audit | `GET /api/cashier/audit-events` | [Audit](../../modules/governance/audit-api.md) | Payment/correction/closure evidence. |

## Explicit Non-Usage

CashierApp does not configure tenant setup, create tenants, prepare station items, deliver service items, or submit customer orders. It must not create QR previews for physical tables.
