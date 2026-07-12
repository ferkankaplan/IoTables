# ServiceStaffApp API Usage

ServiceStaffApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login requirements | `GET /api/auth/login-requirements` | [Identity and Access](../../modules/access/identity-access-api.md) | Safe first-login/setup requirement discovery. |
| Login | `POST /api/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | ServiceStaff app scope. |
| First password setup | `POST /api/auth/first-password/begin`, `POST /api/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | OTP required; code is sent to the tenant identity GSM. |
| Session check/logout | `GET /api/auth/session`, `POST /api/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Human staff session. |
| Authorized halls | `GET /api/service-staff/authorized-halls` | [Staff Access](../../modules/access/staff-access-api.md) | Scope source for service queue filters. |
| Ready items | `GET /api/service-staff/ready-items` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Reads ready PreparationItems and delivery state. |
| Recent deliveries | `GET /api/service-staff/recent-deliveries` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Same-day delivered/recent items for authorized halls. |
| Workload | `GET /api/service-staff/workload` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Hall-scoped counters. |
| Pick up item | `POST /api/service-staff/items/{orderItemId}/pick-up` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Requires item ready and hall scope. |
| Deliver item | `POST /api/service-staff/items/{orderItemId}/deliver` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Direct ready-to-delivered is allowed. |
| Bulk deliver same table | `POST /api/service-staff/items/bulk-deliver` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Requires same-table selection and `Idempotency-Key`. |

## Explicit Non-Usage

ServiceStaffApp does not prepare station items, change setup/menu, receive payments, apply corrections, or close table sessions.
