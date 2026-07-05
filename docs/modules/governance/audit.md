# Module: Audit

## Purpose

Audit owns immutable records of important platform, tenant setup, staff, financial, and operational actions.

It provides traceability for sensitive changes and runtime corrections.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Audit event | Append-only record | create and query |
| Actor reference | Metadata | user/app/system context |
| Target reference | Metadata | tenant/table/session/order/item/payment |
| Reason | Metadata | required for sensitive corrections |

## Not Owned

- Business state itself.
- Authorization decisions.
- Payment calculations.
- Order or session mutation.
- Product analytics, operational KPI calculation, reporting dashboards, or telemetry pipelines.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| PlatformApp | read platform-level audit | Platform scope |
| TenantApp | read tenant setup audit | Own tenant |
| CashierApp | write/read payment/correction/session audit where allowed | Own tenant |
| Staff apps | write operational transition audit | Own tenant, own actions |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Record audit event | Append immutable event | All modules |
| Query tenant audit | Review tenant actions | TenantApp |
| Query platform audit | Review platform actions | PlatformApp |
| Query operational audit | Review payment/correction/session events | CashierApp |

## Internal Rules

- Audit events are append-only.
- Sensitive actions must include actor, tenant, target, action, timestamp.
- Corrections require reason.
- Bootstrap, password setup, OTP verification result, tenant status changes, payments, session closure, delivery/preparation transitions, starter template application, and cashier corrections must be auditable.
- Audit logs should avoid storing secrets or OTP codes.
- Audit records are evidence, not analytics telemetry. Analytics may aggregate from audited events only when the owning app/module source also allows that metric.
- Current release audit retention is indefinite. Automated deletion/archival requires an explicit retention policy later.

Minimum current release action names:

| Action | Required For |
| --- | --- |
| `platform_owner.created` | One-time platform owner bootstrap |
| `platform_owner.totp_enrolled` | Platform Owner TOTP enrollment |
| `tenant.created` | Tenant creation |
| `tenant.provisioning_failed` | Failed tenant provisioning |
| `tenant.activated` | Tenant activation after setup |
| `tenant.suspended` | Tenant suspension |
| `tenant.gsm_changed` | Tenant GSM update |
| `tenant.profile_updated` | Tenant editable profile update outside GSM-only change |
| `starter_template.applied` | One-time starter template application |
| `user.created` | Tenant/platform user creation |
| `user.disabled` | User disable |
| `password.changed` | First password setup or later password change |
| `otp.verified` | Successful OTP verification |
| `venue_layout.changed` | Hall/table setup change |
| `table.disabled` | Table disabled by Tenant Admin |
| `station.changed` | Station setup change |
| `station.disabled` | Station disabled by Tenant Admin |
| `menu_catalog.changed` | Category/product/variant/modifier setup change |
| `availability.changed` | Product or variant availability override |
| `table_display.provisioned` | ESP32/table display provisioning |
| `table_display.revoked` | Display credential revoke/rotation |
| `order.submitted` | Accepted customer order |
| `preparation.status_changed` | Station preparation transition |
| `delivery.status_changed` | Service delivery transition |
| `payment.recorded` | Cashier payment record |
| `payment.voided` | Cashier payment void |
| `session.closed` | Cashier table session closure |
| `cashier.correction_applied` | Any current release cashier correction |

## Operational Safety

- Audit recording should be part of the same transaction when auditing database state changes.
- If external side effects happen, audit should capture request/response state safely without secrets.
- Audit failure policy must be explicit for critical actions.
- Audit event IDs should support reliable correlation.

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| AuditEvent | append-only | tenant nullable, actor nullable, action, targetType, targetId, reason, metadata, createdAt | Critical actions write structured action names; metadata must not contain secrets; actor may be system for provisioning/background work | Append-only; retention policy must preserve critical business/security evidence |
| AuditMetadata | embedded structured value | safe key/value details | No raw secrets, OTP codes, credentials, payment secrets, or raw provider payloads | Stored only as part of AuditEvent |
| AuditReason | required value for sensitive actions | reason text/code | Required for corrections, destructive actions, suspend/reactivate, and manual recovery where specified | Immutable once recorded |

## App Surfaces

| App | Usage |
| --- | --- |
| PlatformApp | Tenant lifecycle and platform changes |
| TenantApp | Setup/staff/menu/layout changes |
| CashierApp | Payments, corrections, closure |
| StationStaffApp | Preparation transitions |
| ServiceStaffApp | Delivery transitions |

## Future Service Boundary

- Own data: audit events and metadata.
- Own APIs: record event, query audit streams.
- Published events: audit.recorded if needed.
- Consumed events: all sensitive domain events.
- Must not leak: secrets, OTP codes, passwords, raw payment provider secrets.

## Open Questions

None currently.
