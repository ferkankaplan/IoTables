# ServiceStaffApp API Usage

ServiceStaffApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login | `POST /api/v1/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | ServiceStaff app scope. |
| First password setup | `POST /api/v1/auth/first-password/begin`, `POST /api/v1/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | No OTP required for service staff in v1. |
| Session check/logout | `GET /api/v1/auth/session`, `POST /api/v1/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Human staff session. |
| Authorized halls | `GET /api/v1/service-staff/authorized-halls` | [Staff Access](../../modules/access/staff-access-api.md) | Scope source for service queue filters. |
| Ready items | `GET /api/v1/service-staff/ready-items` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Reads ready PreparationItems and delivery state. |
| Workload | `GET /api/v1/service-staff/workload` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Hall-scoped counters. |
| Pick up item | `POST /api/v1/service-staff/items/{orderItemId}/pick-up` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Requires item ready and hall scope. |
| Deliver item | `POST /api/v1/service-staff/items/{orderItemId}/deliver` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Direct ready-to-delivered is allowed. |
| Bulk deliver same table | `POST /api/v1/service-staff/items/bulk-deliver` | [Service Delivery](../../modules/fulfillment/service-delivery-api.md) | Requires same-table selection and `Idempotency-Key`. |

## Explicit Non-Usage

ServiceStaffApp does not prepare station items, change setup/menu, receive payments, apply corrections, or close table sessions.
