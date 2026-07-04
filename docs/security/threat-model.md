# Security Threat Model

This document defines the v1 security threat model for IoTables.

It is downstream of:

- [../api/auth.md](../api/auth.md)
- [../api/errors.md](../api/errors.md)
- [../api/idempotency.md](../api/idempotency.md)
- [../modules/access/permission-policy-matrix.md](../modules/access/permission-policy-matrix.md)
- [../modules/_shared/table-access-qr-flow.md](../modules/_shared/table-access-qr-flow.md)
- [../database/transactions.md](../database/transactions.md)
- [../database/indexes-constraints.md](../database/indexes-constraints.md)

## Protection Goals

| Goal | Required Outcome |
| --- | --- |
| Physical table proof | A customer can submit protected table actions only after recently scanning the current QR on that table. |
| Fake order prevention | A photo, replayed QR, stale browser session, or remote caller must not create valid orders. |
| Tenant isolation | Tenant data, staff sessions, customer sessions, QR tokens, display credentials, and runtime records must not cross tenant boundaries. |
| Settlement integrity | Payments, voids, corrections, bill summaries, and session closure must remain server-calculated, authorized, idempotent, and auditable. |
| Duplicate protection | Retries, double clicks, concurrent requests, and worker retries must not create duplicate business records. |
| Secret protection | Raw passwords, OTP codes, session secrets, QR tokens, display credentials, provider payloads, and token hashes must not leak to frontend, logs, audit, or API errors. |
| Fail-closed behavior | Expired, consumed, revoked, disabled, wrong-scope, or stale state must reject mutation without partial business effects. |

## Trust Boundaries

| Boundary | Trusted Evidence | Must Not Trust |
| --- | --- | --- |
| PlatformApp browser | Platform session, CSRF state | Tenant IDs or platform authority from request body |
| Tenant/staff browser | Host tenant, staff session, CSRF, app scope, role/scope checks | Frontend visibility, station/hall IDs, tenant IDs, prices, totals |
| CustomerApp browser | Host tenant, CustomerOrderingSession cookie, fresh QR presence | Customer identity, table IDs, prices, session state from JavaScript |
| ESP32 table display | Active TableDisplayCredential | Tenant/table IDs supplied by device request |
| Background worker | Internal worker identity and claimed outbox row | Business mutation authority outside side-effect processing |
| External providers | Redacted provider result and stable idempotency reference | Provider raw payloads as safe logs or rollback evidence |
| Database | Constraints, locks, transaction boundaries | Frontend-only duplicate prevention or client-side totals |

## Threat Matrix

### QR Replay and Remote Fake Orders

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Attacker photographs QR and submits later | Fake order from outside the table | 60-second `TableAccessToken`, one-time atomic consume, hashed token storage, `token_expired`/`token_consumed` failures. |
| Same QR is redeemed concurrently | Multiple CustomerOrderingSessions or duplicate presence | Atomic consume with one winner; concurrent losers fail without refreshing presence. |
| Browser keeps ordering after leaving table | Orders without current physical presence | Fresh presence required for order submit, table orders, bill summary, and payment summary. Presence expiry does not delete cart. |
| Customer submits trusted table ID manually | Cross-table order or table data read | Backend resolves table from token/session; customer-supplied table IDs are not trusted. |
| QR belongs to another table | Wrong table order | Wrong-table redemption must not mutate the existing CustomerOrderingSession. |

Verification:

- concurrent redemption test has one winner;
- expired/consumed token cannot refresh presence;
- order submit without fresh presence returns `fresh_presence_required`;
- customer table/bill visibility requires fresh presence.

### Customer Session Theft, Loss, or Fixation

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Customer cookie is stolen | Attacker may read session-owned cart/orders | Secure HttpOnly host cookie; fresh QR presence still required for order submit and table-level visibility. |
| Customer cookie is lost | My Orders continuity is lost | Table Orders can recover after fresh QR; old CustomerOrderingSession is not silently merged. |
| Session is fixed across tenants/tables | Cross-tenant or cross-table state | Host tenant and table/session compatibility checked server-side. |
| CSRF on customer cart/order mutation | Unauthorized browser action | Unsafe cookie-auth CustomerApp commands require CSRF. |

Verification:

- customer session cannot cross tenant host;
- fresh QR scan is required before table orders or bill visibility;
- unsafe customer commands reject missing/invalid CSRF.

### Tenant Isolation and App Scope

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Tenant user calls another tenant route | Data leak or unauthorized mutation | Host tenant resolution, session tenant match, composite tenant foreign keys, service guards, and tests. |
| User logs into wrong app surface | Role bypass | App scope validation returns `wrong_app_scope`; frontend routing is not authorization. |
| PlatformApp accesses tenant runtime data | Overreach of platform admin | PlatformApp sees tenant identity/health only unless explicit recovery workflow exists. |
| Suspended tenant continues runtime actions | Orders/payments during suspension | Runtime commands check tenant active state and fail closed. |

Verification:

- cross-tenant IDs return `not_found_or_hidden` or `wrong_scope`;
- disabled/suspended tenant blocks runtime mutations;
- platform session cannot call tenant runtime payment/order commands.

### Authentication, Bootstrap, and OTP Abuse

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Bootstrap credentials remain usable | Default password compromise | First password change is mandatory before normal app workflow. |
| Tenant admin or cashier setup bypasses OTP | Account takeover during bootstrap | Tenant admin and cashier require OTP proof; station/service staff do not require OTP in v1. |
| OTP brute force | Account takeover | OTP lifetime 5 minutes, max 5 verification attempts per challenge, lock after limit. |
| OTP resend abuse | SMS cost and harassment | Max 3 sends per challenge, cooldown between sends, provider errors redacted. |
| Tenant GSM changes during challenge | OTP retargeting confusion | Target GSM is snapshotted when challenge is created; existing challenge target is not silently changed. |
| Login enumeration | Tenant/user discovery | Generic security-sensitive login responses; safe `get_login_requirements` only. |

Verification:

- tenant admin/cashier cannot complete first login without OTP proof;
- concurrent OTP attempts respect the max attempt count;
- OTP code is never stored or logged in plaintext;
- station/service first password setup does not require OTP.

### Duplicate Submit, Replay, and Concurrency

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Customer double-taps order submit | Duplicate orders | `Idempotency-Key` scoped to tenant + CustomerOrderingSession + route + key; request hash conflict returns `idempotency_conflict` or `cart_changed_conflict`. |
| Cashier double-submits payment | Duplicate payment records | Payment idempotency, Check lock, positive amount, recomputed remaining balance. |
| Cashier double-submits correction/void | Duplicate corrections or half-voids | Correction/payment-void idempotency, reason required, Check lock, atomic mutation. |
| Worker retries side effect | Duplicate SMS/provider effects | Outbox `effect_type + idempotency_ref`, worker claim lease, stale claim recovery. |
| Concurrent session close and order submit | Closed session receives order | TableSession/Check locks; order attach fails closed when session is closed. |

Verification:

- duplicate order/payment/void/correction submit returns original compatible result;
- same key with different request returns conflict;
- transaction failure does not expose partial order, payment, correction, queue item, or closure.

### Menu, Price, and Order Tampering

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Customer changes price or total in request | Underpayment or incorrect bill | Client price and frontend totals are ignored; server revalidates and snapshots price at submit. |
| Customer orders unavailable item | Invalid station or kitchen workload | Menu product, variant, modifier, availability, and station are revalidated during submit. |
| Catalog changes after cart creation | Stale cart becomes invalid order | Submit can fail item-level validation and preserve cart for review. |
| Submitted order is edited by customer | Hidden bill manipulation | CustomerApp cannot mutate submitted orders in v1. |

Verification:

- client-supplied totals are ignored;
- stale/unavailable item submit fails without partial order;
- submitted order cannot be mutated by CustomerApp.

### Staff Scope and Operational Role Drift

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Station staff acts outside assigned station | Unauthorized preparation mutation | Station assignment checked at mutation time. |
| Service staff delivers outside assigned hall | Unauthorized delivery mutation | Hall assignment and service delivery tracking checked at mutation time. |
| Revoked staff session keeps old authority | Continued unauthorized operation | Disabled users, revoked roles, and revoked assignments fail server checks as soon as practical. |
| Frontend hides button but API accepts command | Authorization bypass | Backend permission policy is mandatory; frontend visibility is never proof. |

Verification:

- revoked role/assignment blocks subsequent mutation;
- unauthorized station/hall mutation returns `wrong_scope` or module-specific hidden failure;
- service delivery commands fail when service tracking is disabled.

### Cashier and Payment Misuse

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Non-cashier records payment | Unauthorized settlement | Cashier role and own tenant required. |
| Payment exceeds remaining balance | Overpayment or corrupted balance | Server recomputes remaining under Check lock; v1 rejects overpayment. |
| Payment is recorded against closed Check | Closed session mutation | Check must be open. |
| Payment void hides original payment | Audit loss | Void uses immutable fields and required CashierCorrection; original payment is preserved. |
| Correction is reasonless or invalid target | Untraceable bill mutation | Corrections require reason and v1 target eligibility. |
| Customer triggers payment or close | Unauthorized settlement | CustomerApp has read-only bill/payment visibility and cannot mutate settlement. |

Verification:

- payment/correction/void requires cashier role;
- payment over remaining returns `overpayment_not_allowed`;
- closed Check blocks payment/correction/void;
- payment void writes correction and audit atomically.

### ESP32 Display Credential Abuse

| Threat | Impact | Required Controls |
| --- | --- | --- |
| Stolen display credential fetches QR | QR exposure for one table | Credential hash stored; backend resolves tenant/table; TenantApp can revoke/rotate credential. |
| Device sends forged table ID | Cross-table QR exposure | Request table IDs from ESP32 are not trusted. |
| Old credential remains active after reprovisioning | Multiple devices display valid QR | One active credential per tenant/table; rotation revokes old credential first. |
| Display credential appears inside QR | Customer obtains device credential | Display credentials are never embedded in QR payloads. |

Verification:

- revoked credential cannot fetch QR;
- concurrent credential rotation leaves one active credential;
- QR payload contains no display credential.

### External Side Effects and Provider Data

| Threat | Impact | Required Controls |
| --- | --- | --- |
| SMS/provider call runs before domain commit | Side effect references non-committed state | Side effects execute only after source transaction commits. |
| Worker crashes after claim | Lost SMS/provider effect | Bounded claim lease and stale claim recovery. |
| Provider payload leaks secrets | Sensitive data exposure | Store only redacted payload refs/results; no raw OTP, credential, QR, or provider secret in outbox/audit/logs. |
| Provider call cannot roll back | False recovery assumption | Recovery strategy must be explicit; provider idempotency evidence used when available. |

Verification:

- outbox duplicate enqueue is blocked;
- stale claimed outbox row becomes retryable;
- provider failure records redacted state without raw code or secret.

### Error and Logging Disclosure

| Threat | Impact | Required Controls |
| --- | --- | --- |
| API error exposes stack trace, SQL, token, or provider payload | Secret or implementation leak | Error envelope is safe; internal details go to logs by request ID. |
| Audit metadata stores raw secrets | Long-term secret exposure | Audit metadata must be sanitized and tested. |
| Logs include OTP/QR/session/display values | Credential compromise | Log only redacted metadata and hashes when needed for investigation. |
| Platform health leaks tenant runtime detail | Tenant privacy breach | Platform health is high-level and safe only. |

Verification:

- error responses never expose raw secrets or implementation paths;
- audit/outbox/log redaction tests include OTP, QR, session, credential, and provider fields.

## V1 Security Test Matrix

| Area | Required Test Coverage |
| --- | --- |
| QR/presence | Expired token, consumed token, concurrent redeem, wrong-table context, stale presence submit. |
| Customer session | Cross-tenant cookie rejection, CSRF rejection, cookie loss recovery through fresh QR. |
| Idempotency | Duplicate order, duplicate payment, duplicate correction, duplicate payment void, same-key different request. |
| Tenant isolation | Cross-tenant route/ID attempts for staff, customer, display, and cashier APIs. |
| OTP | Max sends, cooldown, max verify attempts, concurrent attempts, no plaintext code logging. |
| Login/session | Disabled user session failure, wrong app scope, platform TOTP gate. |
| Staff scope | Station/hall assignment revocation, unauthorized station/hall mutation, service tracking disabled. |
| Settlement | Overpayment race, closed Check mutation, payment void race, correction eligibility. |
| Side effects | Duplicate enqueue, parallel worker claim, stale claim recovery, redacted provider failure. |
| Disclosure | Error envelope safety, audit metadata sanitizer, response `no-store` for sensitive endpoints. |

## Out of Scope for V1

- Customer payment provider checkout.
- Pay-at-table.
- Fiscal/e-Adisyon/ÖKC integrations.
- Offline-first POS security.
- Device fleet management, firmware health, and remote attestation.
- Multi-location tenant isolation.
- Marketplace, phone, delivery, pickup, and counter-sale channels.

These features require separate threat modeling before implementation.
