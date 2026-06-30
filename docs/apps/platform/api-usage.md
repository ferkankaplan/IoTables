# PlatformApp API Usage

PlatformApp uses platform-global APIs on `https://platform.iotables.net`.

This document maps PlatformApp behavior to module-owned API contracts. It does not redefine endpoint schemas.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login | `POST /api/v1/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Platform Owner scope; TOTP required before dashboard access. |
| Session check | `GET /api/v1/auth/session` | [Identity and Access](../../modules/access/identity-access-api.md) | Used on protected dashboard load. |
| Logout | `POST /api/v1/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Revokes current session. |
| TOTP enrollment | `POST /api/v1/auth/totp/enroll` | [Identity and Access](../../modules/access/identity-access-api.md) | Platform Owner only. |
| Tenant list/health | `GET /api/v1/platform/tenants` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | High-level health only; no tenant runtime leakage. |
| Tenant detail | `GET /api/v1/platform/tenants/{tenantId}` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Identity/profile/lifecycle view. |
| Create tenant | `POST /api/v1/platform/tenants` | [Provisioning](../../modules/platform/provisioning-api.md) | Requires `Idempotency-Key`. |
| Provisioning state | `GET /api/v1/platform/tenants/{tenantId}/provisioning` | [Provisioning](../../modules/platform/provisioning-api.md) | Safe failure summary only. |
| Retry provisioning | `POST /api/v1/platform/tenants/{tenantId}/provisioning/retry` | [Provisioning](../../modules/platform/provisioning-api.md) | Does not rerun completed starter data. |
| Sector options | `GET /api/v1/platform/sectors` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Used by tenant creation form. |
| Starter template preview | `GET /api/v1/platform/sectors/{sector}/starter-template` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Preview only; application is internal to provisioning. |
| DNS readiness | `POST /api/v1/platform/tenants/{tenantId}/dns-ready` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Manual flag; no DNS automation. |
| Lifecycle status | `POST /api/v1/platform/tenants/{tenantId}/status` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Reason required for sensitive transitions. |
| Platform audit | `GET /api/v1/platform/audit-events` | [Audit](../../modules/governance/audit-api.md) | Redacted events only. |
| Side-effect failures | `GET /api/v1/platform/side-effects/failed` | [Reliable Side Effects](../../modules/governance/reliable-side-effects-api.md) | Recovery visibility only. |

## Explicit Non-Usage

PlatformApp does not call tenant runtime mutation APIs for orders, preparation, delivery, payments, table sessions, or customer carts.
