# API Response Standards

This document defines success response shape, common headers, and primitive value formats.

## Envelope Decision

V1 does not use a universal success envelope.

Rules:

- Single-resource queries return the resource object directly.
- Commands return the command result object directly.
- List queries return a list envelope with `items` and `page`.
- Errors always use the error envelope from [errors.md](errors.md).

This keeps API responses simple while still giving lists the metadata they need.

## Single Resource Example

```json
{
  "tenantId": "0d0b4ac6-1e4e-465c-88aa-12b6b2f06f20",
  "name": "Demo Cafe",
  "subdomain": "demo",
  "status": "active"
}
```

## Command Result Example

```json
{
  "orderId": "6567ce0a-efc1-4ee0-8866-e60fd84613b7",
  "tableSessionId": "1a6b6370-ea88-402c-af1d-cf60eb4589b3",
  "submittedAt": "2026-06-30T12:45:00Z"
}
```

## List Response Example

```json
{
  "items": [
    {
      "paymentId": "d74b27c3-bdfc-45c0-96d7-079d36d8db56",
      "amountMinor": 25000,
      "currencyCode": "TRY"
    }
  ],
  "page": {
    "limit": 50,
    "nextCursor": null,
    "hasMore": false
  }
}
```

## Headers

| Header | Rule |
| --- | --- |
| `X-Request-Id` | Returned on every response. |
| `Location` | Returned after create commands when a durable resource URL exists. |
| `Cache-Control` | Use `no-store` for authenticated, customer session, payment, QR, OTP, and admin responses. |

## Field Naming

API JSON fields use `camelCase`.

Examples:

| Domain / DB | API |
| --- | --- |
| `tenant_id` | `tenantId` |
| `created_at` | `createdAt` |
| `amount_minor` | `amountMinor` |
| `currency_code` | `currencyCode` |

## Primitive Formats

| Type | API Format |
| --- | --- |
| UUID | String UUID. |
| Timestamp | ISO 8601 UTC string, for example `2026-06-30T12:45:00Z`. |
| Date | `YYYY-MM-DD` only when a date without time is truly needed. |
| Money | Integer minor units plus `currencyCode`. |
| Boolean | JSON boolean. |
| Enum | `snake_case` string matching domain value sets. |

## Money

Money is never sent as a floating point number.

Use:

```json
{
  "amountMinor": 12500,
  "currencyCode": "TRY"
}
```

Menu prices, order item snapshots, payment amounts, and bill summaries must use minor-unit integers.

## Null and Omitted Fields

- Use `null` when the field is part of the contract and currently unknown/empty.
- Omit fields that are not part of the response for this actor/app.
- Do not include hidden fields with `null` if their existence leaks unauthorized information.

## Redaction

Responses must never include:

- password hashes;
- OTP codes or OTP hashes;
- session token hashes;
- QR token hashes;
- display credential hashes or raw credentials except the one-time credential response during provisioning;
- raw provider payloads;
- stack traces;
- internal SQL errors.
