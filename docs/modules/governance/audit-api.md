# API Contracts: Audit

Source contracts: [audit-contracts.md](audit-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Audit owns append-only critical action records. Apps may query authorized audit views but must not create arbitrary audit records through public HTTP endpoints.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/platform/audit-events` | PlatformApp | `audit.query_platform_audit` | Platform Owner session | Query: `tenantId?`, `action?`, `from?`, `to?`, `cursor`, `limit` | `AuditEventList` | `not_authorized` |
| `GET` | `/api/v1/tenant/audit-events` | TenantApp | `audit.query_tenant_audit` | Tenant Admin session | Query: `action?`, `from?`, `to?`, `cursor`, `limit` | `AuditEventList` | `not_authorized` |
| `GET` | `/api/v1/cashier/audit-events` | CashierApp | `audit.query_operational_audit` | Cashier session | Query: `checkId?`, `tableSessionId?`, `action?`, `from?`, `to?`, `cursor`, `limit` | `AuditEventList` | `missing_role` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `audit.record_event` | No public endpoint. Called by owning modules inside business transactions when possible. |

## Response Schemas

`AuditEvent`:

| Field | Type | Notes |
| --- | --- | --- |
| `auditEventId` | string | Event ID. |
| `tenantId` | string/null | Null only for platform-global events. |
| `actor` | object | Safe actor reference, not raw session token. |
| `action` | string | Allowed audit action. |
| `target` | object | Target type and ID. |
| `reason` | string/null | Present when required. |
| `metadata` | object | Redacted safe metadata only. |
| `createdAt` | timestamp | UTC. |

`AuditEventList` uses cursor pagination.

## Redaction Rules

Audit API responses must never include OTP codes, raw QR tokens, raw display credentials, password hashes, session tokens, provider raw payloads, stack traces, or internal exception details.

## Idempotency

Audit queries do not mutate state. Audit record creation is internal and participates in the caller's transaction/idempotency policy.
