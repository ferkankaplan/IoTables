# Module API Contract Format

Module API contracts define HTTP request/response surfaces for already documented module command/query contracts.

They do not create new product behavior. They wrap app scenarios, module contracts, permission policy, database constraints, and shared API standards.

## Rules

- Put API contracts beside the module that owns the command/query.
- Use `/api/v1`.
- Resolve tenant scope from host/subdomain for tenant-scoped APIs.
- Use `camelCase` JSON fields.
- Use string IDs, ISO 8601 UTC timestamps, and integer minor units for money.
- Do not accept client-supplied trusted `tenantId` on tenant hosts.
- Commands that mutate state require cookie-auth plus `X-CSRF-Token`, unless the caller is a non-browser device/worker using its documented authentication mechanism.
- Commands listed in [../../api/idempotency.md](../../api/idempotency.md) require `Idempotency-Key`.
- Error responses use [../../api/errors.md](../../api/errors.md).
- List responses use [../../api/pagination-filtering.md](../../api/pagination-filtering.md) when pagination is needed.

## Endpoint Table

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `POST` | `/api/v1/example` | App | `module.command` | Required actor | Body/query/header fields | Response fields | Domain/API error codes |

## Response Shape Rule

Use direct resource or command-result objects. Do not introduce a universal success envelope.

Examples:

```json
{
  "tenantId": "ten_...",
  "status": "active"
}
```

For lists:

```json
{
  "items": [],
  "page": {
    "nextCursor": null,
    "hasMore": false
  }
}
```

## Internal Calls

If a module contract is internal-only, say so explicitly. Do not invent an HTTP endpoint just to mirror every internal command.
