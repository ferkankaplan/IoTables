# TenantApp API Usage

TenantApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

This document maps TenantApp behavior to module-owned API contracts. It does not redefine endpoint schemas.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Public tenant page | `GET /api/tenant/context` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Safe public tenant identity only; no GSM, setup, order, or staff data. |
| Login requirements | `GET /api/auth/login-requirements` | [Identity and Access](../../modules/access/identity-access-api.md) | Safe first-login/setup requirements for tenant route. |
| Login | `POST /api/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Tenant Admin scope. |
| Session check | `GET /api/auth/session` | [Identity and Access](../../modules/access/identity-access-api.md) | Used on protected admin routes. |
| Logout | `POST /api/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Revokes current tenant admin session. |
| First password setup | `POST /api/auth/first-password/begin`, `POST /api/auth/first-password/complete` | [Identity and Access](../../modules/access/identity-access-api.md) | Tenant Admin requires OTP proof. |
| OTP state/send/verify | `/api/auth/otp-challenges/{challengeId}...` | [OTP Messaging](../../modules/access/otp-messaging-api.md) | Used only during protected setup flows. |
| Tenant profile | `GET /api/tenant/profile`, `PATCH /api/tenant/profile` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Name/subdomain/status remain immutable to TenantApp. |
| Tenant operational settings | `GET /api/tenant-setup/operational-settings`, `PATCH /api/tenant-setup/operational-settings` | [Tenant Operational Settings](../../modules/tenant-setup/tenant-operational-settings-api.md) | Public display name and service delivery tracking mode. |
| Starter application state | `GET /api/tenant/starter-template-application` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Read-only proof of starter data. |
| Staff management | `/api/tenant/staff...` | [Staff Access](../../modules/access/staff-access-api.md) | Creates bootstrap users and assigns roles/scopes. |
| Hall/table board | `GET /api/tenant-setup/venue/board` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Primary hall management workspace. |
| Hall/table commands | `/api/tenant-setup/halls...`, `/api/tenant-setup/tables...` | [Venue Layout](../../modules/tenant-setup/venue-layout-api.md) | Tables remain managed in hall context. |
| Station setup | `/api/tenant-setup/stations...` | [Station Setup](../../modules/tenant-setup/station-setup-api.md) | Station lifecycle and assignment source. |
| Menu setup | `/api/tenant-setup/menu...` | [Menu Catalog](../../modules/tenant-setup/menu-catalog-api.md) | Prices/routing/availability source. |
| Display provisioning | `/api/tenant-setup/tables/{tableId}/display...` | [Table Display Provisioning](../../modules/tenant-setup/table-display-provisioning-api.md) | Raw claims/secrets returned once. |
| Tenant audit | `GET /api/tenant/audit-events` | [Audit](../../modules/governance/audit-api.md) | Setup/security audit only. |

## Explicit Non-Usage

TenantApp does not receive payments, close table sessions, prepare items, deliver items, or create customer orders.
