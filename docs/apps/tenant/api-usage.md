# TenantApp API Usage

TenantApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

This document maps TenantApp behavior to module-owned API contracts. It does not redefine endpoint schemas.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Public tenant page | `GET /api/v1/tenant/context` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Safe public tenant identity only; no GSM, setup, order, or staff data. |
| Login | `POST /api/v1/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Tenant Admin scope. |
| First password setup | `POST /api/v1/auth/first-password/begin`, `POST /api/v1/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | Tenant Admin requires OTP proof. |
| OTP state/send/verify | `/api/v1/auth/otp-challenges/{challengeId}...` | [OTP Messaging](../../modules/access/otp-messaging-api.md) | Used only during protected setup flows. |
| Tenant profile | `GET /api/v1/tenant/profile`, `PATCH /api/v1/tenant/profile` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Name/subdomain/status remain immutable to TenantApp. |
| Starter application state | `GET /api/v1/tenant/starter-template-application` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Read-only proof of starter data. |
| Staff management | `/api/v1/tenant/staff...` | [Staff Access](../../modules/access/staff-access-api.md) | Creates bootstrap users and assigns roles/scopes. |
| Hall/table board | `GET /api/v1/tenant-setup/venue/board` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Primary hall management workspace. |
| Hall/table commands | `/api/v1/tenant-setup/halls...`, `/api/v1/tenant-setup/tables...` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Tables remain managed in hall context. |
| Station setup | `/api/v1/tenant-setup/stations...` | [Station Setup](../../modules/tenant-setup/station-setup-api.md) | Station lifecycle and assignment source. |
| Menu setup | `/api/v1/tenant-setup/menu...` | [Menu Catalog](../../modules/tenant-setup/menu-catalog-api.md) | Prices/routing/availability source. |
| Display provisioning | `/api/v1/tenant-setup/tables/{tableId}/display...` | [Table Display Provisioning](../../modules/tenant-setup/table-display-provisioning-api.md) | Raw claims/secrets returned once. |
| Tenant audit | `GET /api/v1/tenant/audit-events` | [Audit](../../modules/governance/audit-api.md) | Setup/security audit only. |

## Explicit Non-Usage

TenantApp does not receive payments, close table sessions, prepare items, deliver items, or create customer orders.
