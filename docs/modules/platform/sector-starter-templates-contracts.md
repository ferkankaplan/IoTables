# Module Contracts: Sector Starter Templates

Source module: [sector-starter-templates.md](sector-starter-templates.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `sector_starter_templates.apply_template` | Provisioning | tenantId, sector, templateKey, templateVersion | Caller must hold provisioning lock; template exists and is active; starter application is not `applied` | Insert/update `starter_template_applications`; create normal tenant-owned records in the provisioning transaction; unique tenant/template guard prevents rerun | Applied starter application and created record IDs |
| `sector_starter_templates.mark_failed` | Provisioning | tenantId, templateKey, templateVersion, safe failure summary | Only for failed provisioning transaction/recovery | Lock starter application row; preserve failure summary | Failed or recovery-needed starter state |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `sector_starter_templates.list_sectors` | PlatformApp | none | Platform Owner only in the current release | Supported sector enum and labels |
| `sector_starter_templates.get_template` | PlatformApp, Provisioning | sector/template version | Platform preview or internal provisioning use | Immutable template definition |
| `sector_starter_templates.get_application_state` | PlatformApp, TenantApp, Provisioning | tenantId | Platform all tenants; TenantApp own tenant only | Starter application status and template identity |

## Created Records

The `cafe.v1` template creates tenant-owned records through owning modules:

| Owning Module | Records |
| --- | --- |
| Tenant Setup / Venue Layout | Halls and tables |
| Tenant Setup / Station Setup | Stations |
| Tenant Setup / Menu Catalog | Categories, products, variants, modifiers |
| Access / Identity and Staff Access | Starter users, credentials, staff profiles, roles, assignments |
| Tenant Setup | Tenant operational settings |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `starter_template.applied` | Starter template completes successfully | Audit, Platform health |
| `starter_template.failed` | Starter application fails | Provisioning recovery |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `unsupported_sector` | Selected sector has no active current release starter template. |
| `template_already_applied` | Durable application record is already applied. |
| `template_version_retired` | Requested template cannot be used for new tenants. |
| `starter_record_invalid` | Template would create invalid tenant setup data. |
