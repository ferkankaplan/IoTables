# Module Contracts: Audit

Source module: [audit.md](audit.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `audit.record_event` | Platform, Access, Tenant Setup, Ordering, Fulfillment, Settlement | tenantId nullable, actor, action, target, reason, metadata | Action name allowed; reason required for sensitive actions; metadata sanitized | Insert append-only event in caller transaction where possible | AuditEvent ID |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `audit.query_platform_audit` | PlatformApp | tenantId optional, action/time filters | Platform Owner only | Platform-visible audit events |
| `audit.query_tenant_audit` | TenantApp | tenantId, action/time filters | Tenant Admin own tenant; no platform-only secrets | Tenant setup/security audit events |
| `audit.query_operational_audit` | CashierApp, recovery tooling | tenantId/check/session filters | App-specific permission; sensitive metadata redacted | Corrections/payments/closure/fulfillment audit |

## Minimum Actions

The action names listed in [../../data-model.md](../../data-model.md#otp-audit-and-side-effects) are v1 required. Adding a new sensitive command requires adding its audit action before implementation.

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `audit_reason_required` | Sensitive action lacked a reason. |
| `metadata_not_safe` | Metadata includes secrets, raw provider payloads, OTPs, tokens, or credentials. |
| `unknown_action` | Action name is not in the allowed audit catalog. |
