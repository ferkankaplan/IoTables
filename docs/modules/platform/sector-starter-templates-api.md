# API Contracts: Sector Starter Templates

Source contracts: [sector-starter-templates-contracts.md](sector-starter-templates-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Sector Starter Templates expose only safe PlatformApp selection and template application state. Applying a template is internal to Provisioning.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/platform/sectors` | PlatformApp | `sector_starter_templates.list_sectors` | Platform Owner session | none | `SectorList` | `not_authorized` |
| `GET` | `/api/v1/platform/sectors/{sector}/starter-template` | PlatformApp | `sector_starter_templates.get_template` | Platform Owner session | Path: `sector`; query: `version?` | `StarterTemplatePreview` | `unsupported_sector`, `template_version_retired` |
| `GET` | `/api/v1/platform/tenants/{tenantId}/starter-template-application` | PlatformApp | `sector_starter_templates.get_application_state` | Platform Owner session | Path: `tenantId` | `StarterTemplateApplicationState` | `not_authorized`, `not_found_or_hidden` |
| `GET` | `/api/v1/tenant/starter-template-application` | TenantApp | `sector_starter_templates.get_application_state` | Tenant Admin session | Host-derived tenant | `StarterTemplateApplicationState` | `not_authorized` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `sector_starter_templates.apply_template` | No public endpoint. Called by Provisioning while holding the provisioning lock. |
| `sector_starter_templates.mark_failed` | No public endpoint. Called by Provisioning/recovery flow with a redacted failure summary. |

## Response Schemas

`SectorList`:

| Field | Type | Notes |
| --- | --- | --- |
| `items` | array | Each item includes `sector`, `label`, `defaultTemplateKey`, `defaultTemplateVersion`, `active`. |

`StarterTemplatePreview`:

| Field | Type | Notes |
| --- | --- | --- |
| `sector` | string enum | Sector. |
| `templateKey` | string | Example: `cafe`. |
| `templateVersion` | string/integer | Immutable template version. |
| `creates` | object | Counts, labels, and safe price preview for halls, tables, stations, products, and starter roles. |

`StarterTemplateApplicationState`:

| Field | Type | Notes |
| --- | --- | --- |
| `tenantId` | string | Tenant. |
| `templateKey` | string/null | Applied or attempted template. |
| `templateVersion` | string/integer/null | Applied or attempted version. |
| `status` | string enum | `not_selected`, `pending`, `applied`, `failed`, `recovery_needed`. |
| `appliedAt` | timestamp/null | Set once. |
| `failureSummary` | string/null | Redacted only. |

## Idempotency

No public endpoint here mutates starter data. The one-time application guarantee belongs to Provisioning and the `starter_template_applications` database uniqueness rule.
