# API Standards

This folder defines shared API rules for IoTables before endpoint-specific request/response contracts are written.

API contracts sit above module command/query contracts. They must not weaken module ownership, permission guards, idempotency, transaction rules, or domain failure semantics.

## Documents

| Document | Purpose |
| --- | --- |
| [auth.md](auth.md) | Session, cookie, CSRF, tenant resolution, CustomerApp, ESP32, and worker authentication standards. |
| [responses.md](responses.md) | Success response shape, JSON naming, IDs, timestamps, money, and headers. |
| [errors.md](errors.md) | Error envelope, error code rules, HTTP status mapping, validation errors, and redaction. |
| [idempotency.md](idempotency.md) | `Idempotency-Key` requirements, request hashing, duplicate handling, and retention. |
| [pagination-filtering.md](pagination-filtering.md) | Cursor pagination, filtering, sorting, and list response standards. |

## Source Order

When designing an endpoint, resolve semantics in this order:

1. App scenario and UI need.
2. Module command/query contract.
3. Permission policy matrix.
4. Database transaction/idempotency/constraint rule.
5. API standard in this folder.
6. Endpoint-specific request/response contract.

If an endpoint needs behavior missing from app or module documents, update those semantic sources first.

## Versioning

V1 APIs use:

```text
/api/v1
```

Breaking API changes require either:

- a new version path, or
- an explicitly approved coordinated frontend/backend release where no old client remains supported.

Do not create versioned behavior through hidden request flags.

## HTTP Method Rules

| Method | Use |
| --- | --- |
| `GET` | Queries only. Must not mutate business state. |
| `POST` | Commands that create records, trigger transitions, submit orders, record payments, verify OTP, or perform action-style workflows. |
| `PATCH` | Partial update of editable resource fields where the resource remains the same concept. |
| `DELETE` | Avoid for v1 business records. Use disable, revoke, close, void, abandon, or correction commands instead. |

Action-style domain transitions should be explicit commands, not hidden `PATCH` side effects.

Examples:

```text
POST /api/v1/station-staff/preparation-items/{preparationItemId}/start
POST /api/v1/station-staff/preparation-items/{preparationItemId}/mark-ready
POST /api/v1/cashier/checks/{checkId}/payments
POST /api/v1/cashier/table-sessions/{tableSessionId}/close
```

Endpoint-specific contracts define the authoritative route, actor, authentication, request, response, and failure-code details.

## JSON Rules

- Request and response bodies are JSON.
- Field names use `camelCase`.
- IDs are strings.
- Timestamps are ISO 8601 UTC strings.
- Money uses integer minor units plus currency code. No floating point money values.
- Unknown request fields should be rejected for command payloads.
- Response bodies must not include secrets, token hashes, password hashes, OTP codes, display credentials, raw provider payloads, or stack traces.

## Required Headers

| Header | Direction | Rule |
| --- | --- | --- |
| `Content-Type: application/json` | Request | Required for requests with JSON body. |
| `Accept: application/json` | Request | Recommended for API clients. |
| `X-Request-Id` | Request/Response | Client may send; server must return one. |
| `Idempotency-Key` | Request | Required for commands listed in [idempotency.md](idempotency.md). |
| `X-CSRF-Token` | Request | Required for unsafe methods using cookie-auth sessions. |

## Tenant Resolution

Tenant APIs resolve tenant from the request host/subdomain, not from client-supplied `tenantId`.

| Host | Meaning |
| --- | --- |
| `platform.iotables.net` | PlatformApp and platform APIs. |
| `[tenant].iotables.net` | TenantApp, CustomerApp, StationStaffApp, ServiceStaffApp, CashierApp, tenant-scoped APIs. |

Platform APIs may accept `tenantId` as a target identifier because PlatformApp is global. Tenant-scoped APIs must treat body/query `tenantId` as informational at most and must not trust it for authorization.

## Open Questions

None currently.
