# API Idempotency Standards

This document defines HTTP-level idempotency rules.

Module contracts and database constraints still own the deeper operation-specific guarantees.

## Header

Use:

```text
Idempotency-Key: <client-generated-key>
```

Rules:

- Required for listed non-idempotent commands.
- Recommended format is UUID or another high-entropy opaque string.
- Maximum length: 128 characters.
- Treat keys as opaque; do not encode business meaning in them.
- Scope keys by actor/session, tenant, route/operation, and target aggregate where applicable.

## Required Commands

A command becomes header-required only after its module contract and database model define where the idempotency key, request hash, status, and replay result are stored.

| Command | Why |
| --- | --- |
| `provisioning.start_tenant` | Prevent duplicate tenant creation attempts beyond subdomain uniqueness. |
| `customer_ordering.submit_order` | Prevent duplicate customer orders from double-click/retry. |
| `payments.record_payment` | Prevent duplicate payment records. |
| `payments.void_payment` | Prevent duplicate payment void/correction records. |
| `table_session_billing.record_cashier_correction` | Prevent duplicate cashier correction records. |
| `service_delivery.bulk_mark_delivered` | Prevent partial or duplicate same-table bulk delivery transitions. |

## State-Guarded Commands

These commands are protected by domain state checks, locks, unique constraints, and audit/correction rules. They may accept an `Idempotency-Key`, but v1 must not require it until the persistence model explicitly defines storage and replay behavior.

| Command | Current Guard |
| --- | --- |
| `table_session_billing.close_session` | TableSession/check locks; zero-balance guard; unique session closure. |

Commands with one-time secrets may not require this header when the one-time secret is the idempotency guard:

| Command | Guard |
| --- | --- |
| `table_presence.redeem_token` | One-time QR token atomic consume. |
| `table_display.consume_claim` | One-time display claim atomic consume. |
| `otp_messaging.verify_otp` | Challenge attempt accounting and idempotent success. |

## Request Hash

For required idempotency keys, store a server-computed normalized request hash. Clients send `Idempotency-Key`; they do not send a trusted request hash.

Same key + same request:

- return the original successful result;
- or return current processing state if still in progress.

Same key + different request:

- return `409 Conflict`;
- code: `idempotency_conflict`.

## Response Behavior

| Situation | Response |
| --- | --- |
| First successful request | Normal success response. |
| Exact duplicate after success | Same domain result as original request. |
| Duplicate while processing | `409 Conflict` with `request_processing` or a documented pending response for that endpoint. |
| Same key with different request | `409 Conflict` with `idempotency_conflict`. |
| Expired idempotency record | Treat as new only if retention policy says retry window has passed and operation semantics allow it. |

## Storage and Retention

| Operation | Minimum Retention |
| --- | --- |
| Order submit | Long enough to cover mobile/browser retries; v1 target at least 24 hours. |
| Payment record | Long enough to cover cashier/network retries and audit; v1 target at least 7 days. |
| Payment void | Preserve with payment audit history. |
| Cashier correction | Preserve with correction audit history. |
| Tenant provisioning | Preserve with tenant/provisioning history. |
| Bulk delivery | Long enough to cover service staff retries and same-day operational audit; v1 target at least 24 hours. |

Retention can be tightened later only after operational requirements are known.

## Frontend Rules

- Generate an idempotency key before enabling the submit action.
- Reuse the same key for automatic retry of the same user action.
- Generate a new key when the user changes the request.
- Disable pending buttons, but never rely on disabled buttons as the only duplicate-submit defense.

## Backend Rules

- Reserve idempotency before performing irreversible work.
- Use a transaction and database uniqueness to protect the reservation.
- Do not store raw secrets in idempotency records.
- Do not allow client-provided totals/prices to become trusted because they are inside an idempotent request.
