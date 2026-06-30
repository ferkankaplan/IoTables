# API Contracts: Provisioning

Source contracts: [provisioning-contracts.md](provisioning-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Provisioning owns tenant creation orchestration. It is the only public PlatformApp route that creates a tenant.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/v1/platform/tenants` | PlatformApp | `provisioning.start_tenant` | Platform Owner session + CSRF + `Idempotency-Key` | Body: `CreateTenantRequest` | `ProvisioningResult` | `duplicate_subdomain`, `unsupported_sector`, `provisioning_incomplete`, `recovery_required` |
| `GET` | `/api/v1/platform/tenants/{tenantId}/provisioning` | PlatformApp | `provisioning.get_state` | Platform Owner session | Path: `tenantId` | `ProvisioningState` | `not_authorized`, `not_found_or_hidden` |
| `GET` | `/api/v1/platform/tenants/{tenantId}/provisioning/recovery-summary` | PlatformApp | `provisioning.get_recovery_summary` | Platform Owner session | Path: `tenantId` | `ProvisioningRecoverySummary` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/v1/platform/tenants/{tenantId}/provisioning/retry` | PlatformApp | `provisioning.retry_failed` | Platform Owner session + CSRF | Body: `recoveryNote?` | `ProvisioningState` | `starter_already_applied`, `recovery_required`, `invalid_lifecycle_transition` |
| `POST` | `/api/v1/platform/tenants/{tenantId}/provisioning/recovery-needed` | Platform recovery tooling | `provisioning.mark_recovery_needed` | Platform Owner/recovery session + CSRF | Body: `reason` | `ProvisioningState` | `not_authorized`, `reason_required` |

## Request Schemas

`CreateTenantRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Immutable tenant name. |
| `subdomain` | string | yes | Immutable normalized subdomain. |
| `gsmNumber` | string | yes | Used for first-password OTP. |
| `sector` | string enum | no | If present, applies one starter template once. |
| `capacity` | integer | no | Optional restaurant capacity. |
| `address` | object/string | no | Optional address. |

`ProvisioningRetryRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `recoveryNote` | string | no | Safe operator note. Must not include secrets. |

## Response Schemas

`ProvisioningResult`:

| Field | Type | Notes |
| --- | --- | --- |
| `tenantId` | string | Reserved tenant. |
| `status` | string enum | `active`, `provisioning_failed`, or `recovery_needed`. |
| `subdomain` | string | Immutable tenant subdomain. |
| `starterTemplateApplied` | boolean | True only when template application committed. |
| `failureSummary` | string/null | Redacted safe failure summary. |
| `dnsReady` | boolean | Manual platform flag; provisioning does not automate DNS. |

`ProvisioningState` includes `tenantId`, `tenantStatus`, `starterApplicationStatus`, `templateKey`, `templateVersion`, `failureSummary`, `dnsReady`, `createdAt`, and `updatedAt`.

`ProvisioningRecoverySummary` includes `tenantId`, `missingRequiredRecords`, `completedPhases`, `failedPhase`, `safeRetryAllowed`, and redacted `failureSummary`.

## Idempotency

`POST /api/v1/platform/tenants` requires `Idempotency-Key`.

Same key and same normalized request returns the original `ProvisioningResult`. Same key with a different normalized request returns `409 idempotency_conflict`.

Tenant creation still relies on database uniqueness for normalized subdomain. Idempotency is not a replacement for the unique tenant identity constraint.
