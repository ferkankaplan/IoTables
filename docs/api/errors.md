# API Error Standards

This document defines the current release error envelope and HTTP status mapping.

Module contracts define domain failure names. API endpoints map those failures to HTTP status codes and this envelope.

## Error Envelope

All API errors use:

```json
{
  "error": {
    "code": "fresh_presence_required",
    "message": "Fresh table QR scan is required.",
    "requestId": "req_01JZ0000000000000000000000",
    "details": {},
    "fieldErrors": []
  }
}
```

| Field | Rule |
| --- | --- |
| `error.code` | Stable machine-readable `snake_case` code. |
| `error.message` | Safe human-readable message for the current app. |
| `error.requestId` | Same value as `X-Request-Id`. |
| `error.details` | Optional safe structured metadata. |
| `error.fieldErrors` | Optional validation errors for specific fields. |

Do not expose stack traces, SQL messages, provider raw payloads, secrets, token values, or internal implementation paths.

Frontend surfaces must not show backend fallback text directly when a stable `error.code`
exists. User-facing apps translate known error codes into short Turkish action messages
and may append the `requestId` for support/debugging. Backend messages remain safe
fallbacks and API diagnostics, not the primary UX copy source.

## Field Errors

Use `fieldErrors` for request validation problems:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "Some fields are invalid.",
    "requestId": "req_01JZ0000000000000000000000",
    "details": {},
    "fieldErrors": [
      {
        "path": "items[0].quantity",
        "code": "must_be_positive",
        "message": "Quantity must be greater than zero."
      }
    ]
  }
}
```

Field error paths use API JSON field names, not Python or database names.

## HTTP Status Mapping

| HTTP Status | Use | Example Codes |
| --- | --- | --- |
| `400 Bad Request` | Malformed JSON, invalid query syntax, unsupported header shape | `bad_request`, `malformed_json` |
| `401 Unauthorized` | No valid session/credential or expired login | `unauthenticated`, `session_expired`, `invalid_credentials` |
| `403 Forbidden` | Authenticated but not allowed | `not_authorized`, `wrong_app_scope`, `wrong_scope`, `csrf_failed` |
| `404 Not Found` | Resource absent or intentionally hidden from actor | `not_found_or_hidden` |
| `409 Conflict` | Current state or idempotency conflict prevents command | `invalid_state`, `conflicting_request`, `duplicate_subdomain`, `check_closed` |
| `410 Gone` | One-time/temporary access artifact is expired or consumed | `token_expired`, `token_consumed`, `claim_expired`, `claim_consumed` |
| `422 Unprocessable Entity` | Structurally valid request fails field/domain validation | `validation_failed`, `item_not_orderable`, `overpayment_not_allowed` |
| `429 Too Many Requests` | Rate limit exceeded | `rate_limit_exceeded`, `otp_locked` |
| `500 Internal Server Error` | Unexpected server failure | `internal_error` |
| `503 Service Unavailable` | Tenant/app temporarily unavailable or dependency outage | `tenant_unavailable`, `provider_unavailable` |

Security-sensitive login and lookup failures may use generic messages to avoid account or tenant enumeration.

## Domain Failure Mapping

| Domain Failure | HTTP Status | API Code |
| --- | --- | --- |
| `fresh_presence_required` | 403 | `fresh_presence_required` |
| `not_authorized` | 403 | `not_authorized` |
| `wrong_scope` | 403 | `wrong_scope` |
| `not_found_or_hidden` | 404 | `not_found_or_hidden` |
| `duplicate_request` | 200 or original success status | Return original idempotent result |
| `conflicting_request` | 409 | `idempotency_conflict` |
| `invalid_state` | 409 | Domain-specific code where useful |
| `duplicate_subdomain` | 409 | `duplicate_subdomain` |
| `otp_expired` | 410 | `otp_expired` |
| `otp_invalid` | 422 | `otp_invalid` |
| `otp_locked` | 429 | `otp_locked` |
| `overpayment_not_allowed` | 422 | `overpayment_not_allowed` |

## Validation Policy

- Reject unknown fields for command requests.
- Reject client-supplied trusted values such as totals, price authority, tenant scope, station scope, or permission scope.
- Use safe app-facing messages.
- Put detailed internal diagnostics in logs with the request ID, not in the response.

## Request ID

Every error response must include:

- `X-Request-Id` response header;
- `error.requestId` body field.

If the client does not send `X-Request-Id`, the server generates one.
