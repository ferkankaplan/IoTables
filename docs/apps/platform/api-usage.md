# PlatformApp API Usage

PlatformApp uses platform-global APIs on `https://platform.iotables.net`.

This document maps PlatformApp behavior to module-owned API contracts. It does not redefine endpoint schemas.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Login requirements | `GET /api/auth/login-requirements` | [Identity and Access](../../modules/access/identity-access-api.md) | Safe setup requirement discovery; no tenant data exposure. |
| Login | `POST /api/auth/login` | [Identity and Access](../../modules/access/identity-access-api.md) | Platform Owner scope; username/password only in the current release. |
| Session check | `GET /api/auth/session` | [Identity and Access](../../modules/access/identity-access-api.md) | Used on protected dashboard load. |
| Logout | `POST /api/auth/logout` | [Identity and Access](../../modules/access/identity-access-api.md) | Revokes current session. |
| TOTP enrollment | `POST /api/auth/totp/enroll` | [Identity and Access](../../modules/access/identity-access-api.md) | Reserved for future PlatformApp hardening; not used by current release PlatformApp login. |
| Tenant list/health | `GET /api/platform/tenants` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | High-level health only; no tenant runtime leakage. |
| Tenant detail | `GET /api/platform/tenants/{tenantId}` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Identity/profile/lifecycle view. |
| Update tenant profile | `PATCH /api/platform/tenants/{tenantId}/profile` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Editable platform-owned fields only; name/subdomain remain immutable. |
| Create tenant | `POST /api/platform/tenants` | [Provisioning](../../modules/platform/provisioning-api.md) | Requires `Idempotency-Key`. |
| Provisioning state | `GET /api/platform/tenants/{tenantId}/provisioning` | [Provisioning](../../modules/platform/provisioning-api.md) | Safe failure summary only. |
| Provisioning recovery summary | `GET /api/platform/tenants/{tenantId}/provisioning/recovery-summary` | [Provisioning](../../modules/platform/provisioning-api.md) | Safe recovery inspection only; no runtime rewrite. |
| Retry provisioning | `POST /api/platform/tenants/{tenantId}/provisioning/retry` | [Provisioning](../../modules/platform/provisioning-api.md) | Does not rerun completed starter data. |
| Sector options | `GET /api/platform/sectors` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Used by tenant creation form. |
| Starter template preview | `GET /api/platform/sectors/{sector}/starter-template` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Preview only; application is internal to provisioning. |
| Starter application state | `GET /api/platform/tenants/{tenantId}/starter-template-application` | [Sector Starter Templates](../../modules/platform/sector-starter-templates-api.md) | Shows one-time starter application state. |
| DNS readiness | `POST /api/platform/tenants/{tenantId}/dns-ready` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Manual flag; no DNS automation. |
| Lifecycle status | `POST /api/platform/tenants/{tenantId}/status` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Reason required for sensitive transitions. |
| Tenant lifecycle events | `GET /api/platform/tenants/{tenantId}/lifecycle-events` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Lifecycle timeline for selected tenant detail/audit. |
| Platform audit | `GET /api/platform/audit-events` | [Audit](../../modules/governance/audit-api.md) | Redacted events only. |
| Side-effect failures | `GET /api/platform/side-effects/failed` | [Reliable Side Effects](../../modules/governance/reliable-side-effects-api.md) | Recovery visibility only. |

## Explicit Non-Usage

PlatformApp does not call tenant runtime mutation APIs for orders, preparation, delivery, payments, table sessions, or customer carts.
