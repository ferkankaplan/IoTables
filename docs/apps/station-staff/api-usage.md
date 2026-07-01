# StationStaffApp API Usage

StationStaffApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login requirements | `GET /api/v1/auth/login-requirements` | [Identity and Access](../../modules/access/identity-access-api.md) | Safe first-login/setup requirement discovery. |
| Login | `POST /api/v1/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | StationStaff app scope. |
| First password setup | `POST /api/v1/auth/first-password/begin`, `POST /api/v1/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | No OTP required for station staff in v1. |
| Session check/logout | `GET /api/v1/auth/session`, `POST /api/v1/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Human staff session. |
| Authorized stations | `GET /api/v1/station-staff/authorized-stations` | [Staff Access](../../modules/access/staff-access-api.md) | Scope source for queue filters. |
| Station context | `GET /api/v1/station-staff/stations/{stationId}/context` | [Station Setup](../../modules/tenant-setup/station-setup-api.md) | Validates station visibility. |
| Station queue | `GET /api/v1/station-staff/queue` | [Preparation](../../modules/fulfillment/preparation-api.md) | Only assigned stations. |
| Recent/completed items | `GET /api/v1/station-staff/recent-items` | [Preparation](../../modules/fulfillment/preparation-api.md) | Same-day recent items for assigned station. |
| Workload | `GET /api/v1/station-staff/workload` | [Preparation](../../modules/fulfillment/preparation-api.md) | Counts/age for assigned station. |
| Start preparing | `POST /api/v1/station-staff/preparation-items/{preparationItemId}/start` | [Preparation](../../modules/fulfillment/preparation-api.md) | `pending -> preparing`. |
| Mark ready | `POST /api/v1/station-staff/preparation-items/{preparationItemId}/mark-ready` | [Preparation](../../modules/fulfillment/preparation-api.md) | `preparing -> ready`. |
| Cannot prepare | `POST /api/v1/station-staff/preparation-items/{preparationItemId}/cannot-prepare` | [Preparation](../../modules/fulfillment/preparation-api.md) | Reason required. |

## Explicit Non-Usage

StationStaffApp does not change menu setup, delivery state, payments, corrections, or table session closure.
