# Platform Context

Platform owns tenant identity, lifecycle, provisioning, and platform-only operational control.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [tenant-registry.md](tenant-registry.md) | Tenant identity, subdomain, GSM, lifecycle, availability |
| [provisioning.md](provisioning.md) | Tenant creation orchestration and recovery state |
| [sector-starter-templates.md](sector-starter-templates.md) | One-time starter data templates by sector |

## Contract Documents

| Contract | Purpose |
| --- | --- |
| [tenant-registry-contracts.md](tenant-registry-contracts.md) | Tenant identity, profile, lifecycle, health, and subdomain commands/queries |
| [provisioning-contracts.md](provisioning-contracts.md) | Tenant provisioning and recovery commands/queries |
| [sector-starter-templates-contracts.md](sector-starter-templates-contracts.md) | Sector starter template application and state contracts |

## API Documents

| API Contract | Purpose |
| --- | --- |
| [tenant-registry-api.md](tenant-registry-api.md) | Tenant profile, lifecycle, health, and tenant context endpoints |
| [provisioning-api.md](provisioning-api.md) | Tenant creation, provisioning state, retry, and recovery endpoints |
| [sector-starter-templates-api.md](sector-starter-templates-api.md) | Sector list, starter template preview, and starter application state endpoints |

## Primary Apps

- PlatformApp
- TenantApp read access for own tenant identity/profile
- CustomerApp, CashierApp, StationStaffApp, and ServiceStaffApp read tenant availability through trusted subdomain resolution

## Boundary Rule

Platform may create and control tenant lifecycle, but it must not directly mutate tenant runtime records such as orders, sessions, payments, preparation, or delivery.
