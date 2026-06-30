# Platform Context

Platform owns tenant identity, lifecycle, provisioning, and platform-only operational control.

## Internal Modules

| Module | Purpose |
| --- | --- |
| [tenant-registry.md](tenant-registry.md) | Tenant identity, subdomain, GSM, lifecycle, availability |
| [provisioning.md](provisioning.md) | Tenant creation orchestration and recovery state |
| [sector-starter-templates.md](sector-starter-templates.md) | One-time starter data templates by sector |

## Primary Apps

- PlatformApp
- TenantApp read access for own tenant identity/profile
- CustomerApp, CashierApp, StationStaffApp, and ServiceStaffApp read tenant availability through trusted subdomain resolution

## Boundary Rule

Platform may create and control tenant lifecycle, but it must not directly mutate tenant runtime records such as orders, sessions, payments, preparation, or delivery.
