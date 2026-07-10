# Transaction and Concurrency Catalog

This document defines the current release transaction, locking, idempotency, rollback, and concurrency behavior for critical IoTables flows.

It is downstream of:

- [../apps](../apps/README.md)
- [../modules](../modules/README.md)
- [../data-model.md](../data-model.md)
- [schema.md](schema.md)
- [indexes-constraints.md](indexes-constraints.md)
- [seed-provisioning.md](seed-provisioning.md)
- [../api/idempotency.md](../api/idempotency.md)

It does not invent product behavior. If this catalog conflicts with app or module semantics, update the app/module source first, then this catalog.

## Global Rules

| Rule | Requirement |
| --- | --- |
| Source order | App scenario -> module contract -> data model -> database constraint -> API response. |
| Transaction scope | Keep transactions short and centered on one business decision. |
| External side effects | SMS, email, provider calls, DNS, and device communication are never assumed to roll back with the database. |
| Idempotency reservation | Commands requiring `Idempotency-Key` reserve the idempotency row before mutating business records. |
| Request hash | The API layer computes request hashes from server-trusted inputs. Clients never provide trusted hashes. |
| Replay result | Successful idempotent replay returns the original domain result. |
| Different request, same key | Return `409 idempotency_conflict`. |
| Processing duplicate | Return `409 request_processing` unless the endpoint documents a pending response. |
| No partial visibility | Failed transactions must not expose partial orders, payments, corrections, queue items, delivery states, or closures. |
| Read models | Rebuildable read models may update in the same transaction or be rebuilt after commit, but source records are authoritative. |

## Lock Ordering Rules

Use explicit row locks where concurrent mutation can corrupt state. Acquire locks in the order below when a transaction touches more than one group.

| Order | Lock Group | Examples |
| --- | --- | --- |
| 1 | Idempotency or one-time secret guard | `tenant_provisioning_idempotency`, `order_submit_idempotency`, `payment_idempotency`, consumed QR/firmware row |
| 2 | Tenant/provisioning aggregate when provisioning or lifecycle is being changed | `tenants`, `starter_template_applications` |
| 3 | Parent runtime aggregate | `table_sessions`, `checks` |
| 4 | Target business records in deterministic ID order | `orders`, `order_items`, `payments`, `preparation_items`, `delivery_states` |
| 5 | Append-only records | transition rows, corrections, audit events, outbox messages |

Settlement mutations that involve a Check must lock the Check before child financial records such as Payments. This keeps payment record, payment void, cashier correction, and close-session flows on one parent-first lock order.

For multi-row item operations, sort target IDs before locking. Never lock the same set in caller-provided order.

## Critical Flow Catalog

### Tenant Creation and Starter Template

| Field | Decision |
| --- | --- |
| Apps | PlatformApp |
| Owner modules | Provisioning, Tenant Registry, Identity and Access, Staff Access, Sector Starter Templates, Tenant Setup, Audit |
| Public command/API | `provisioning.start_tenant`, `POST /api/platform/tenants` |
| Idempotency | Required. Store reservation/result in `tenant_provisioning_idempotency`; scope by platform actor + route + normalized tenant identity + idempotency key. |
| Lock order | Phase 1 reserves tenant identity. Phase 2 locks `tenants`, then `starter_template_applications`, then creates owned records. |
| Transaction boundary | Phase 1 short reservation transaction. Phase 2 one locked transaction for required records and starter data. Phase 3 separate failure-marking transaction when Phase 2 fails. |
| Rollback | Phase 2 rollback removes tenant admin/starter business records from that failed attempt. Failure marking preserves safe recovery state. |
| Concurrency response | Duplicate subdomain returns `duplicate_subdomain`. Same idempotency key/request returns original result. Same key/different request returns `idempotency_conflict`. |
| Test requirement | Duplicate tenant create, starter apply exactly once, Phase 2 failure rollback, retry failed provisioning, no rerun after sector change. |

### Provisioning Retry

| Field | Decision |
| --- | --- |
| Apps | PlatformApp recovery tooling |
| Owner modules | Provisioning, Sector Starter Templates, Tenant Registry |
| Public command/API | `provisioning.retry_failed`, `POST /api/platform/tenants/{tenantId}/provisioning/retry` |
| Idempotency | State-guarded; no required `Idempotency-Key` in the current release. |
| Lock order | Lock `tenants`, then `starter_template_applications`. |
| Transaction boundary | Retry only the incomplete phase while holding provisioning locks. |
| Rollback | Failed retry leaves previous safe failure history and updates recovery state only in a separate failure transaction. |
| Concurrency response | Already applied starter returns `starter_already_applied` or existing applied state; unsafe retry returns `recovery_required`. |
| Test requirement | Concurrent retry cannot apply starter records twice. Active tenant with applied starter is never reseeded. |

### Table Display Firmware Generation

| Field | Decision |
| --- | --- |
| Apps | TenantApp setup surface |
| Owner modules | Table Display Provisioning |
| Public command/API | `table_display.generate_firmware`, `POST /api/tenant-setup/tables/{tableId}/display-firmware` |
| Idempotency | State-guarded by table credential lock and one-time firmware artifact; no `Idempotency-Key`. |
| Lock order | Lock tenant/table credential rows; revoke previous active credential; insert new credential; insert one-time firmware metadata. |
| Transaction boundary | Previous credential revocation, new credential creation, firmware metadata, and audit commit together. |
| Rollback | If firmware metadata or credential creation fails, previous credential remains active because the transaction rolls back. |
| Concurrency response | Concurrent generations serialize on the table credential lock; the final committed generation owns the only active credential. |
| Test requirement | Concurrent generation attempts leave one active credential and one valid one-time firmware download. Raw WiFi password is never persisted. |

### Table Display Credential Rotation or Revocation

| Field | Decision |
| --- | --- |
| Apps | TenantApp |
| Owner modules | Table Display Provisioning |
| Public command/API | `table_display.rotate_credential`, `table_display.revoke_credential` |
| Idempotency | State-guarded and audited; no required `Idempotency-Key` in the current release. |
| Lock order | Lock tenant/table credential rows for the target table. |
| Transaction boundary | Rotation revokes old active credential and inserts replacement in one transaction. Revocation marks credential revoked and writes audit in one transaction. |
| Rollback | Failed rotation leaves the old credential active. Failed revocation leaves credential unchanged. |
| Concurrency response | Concurrent rotate/revoke serializes on the table credential lock; stale request returns current state or `credential_revoked`. |
| Test requirement | Concurrent rotations leave one active credential. Revoked credential cannot fetch QR. |

### QR Token Issue

| Field | Decision |
| --- | --- |
| Apps | ESP32 table display |
| Owner modules | Table Presence, Table Display Provisioning |
| Public command/API | `table_presence.issue_current_qr_token`, `GET /api/table-display/qr-token` |
| Idempotency | State-guarded by display credential and active token lifecycle; no `Idempotency-Key`. |
| Lock order | Authenticate credential, then lock display/table token issuance path. |
| Transaction boundary | Create or return the current live unconsumed token under lock. |
| Rollback | Failed token insert returns no raw token and leaves prior current token unchanged. |
| Concurrency response | Concurrent display polls must not create multiple live unconsumed tokens for the same display. |
| Test requirement | Parallel QR fetches produce one current token or the same current token until refresh rules allow rotation. |

### QR Token Redeem and Customer Session Refresh

| Field | Decision |
| --- | --- |
| Apps | CustomerApp |
| Owner modules | Table Presence, Customer Ordering |
| Public command/API | `table_presence.redeem_token`, `POST /api/customer/table-presence/redeem` |
| Idempotency | One-time QR token is the guard; no `Idempotency-Key`. |
| Lock order | Atomic update/consume `table_access_tokens`; lock compatible `customer_ordering_sessions` row when cookie exists; create/refresh session. |
| Transaction boundary | Token consume and CustomerOrderingSession presence refresh commit together. |
| Rollback | If session refresh fails, token consume rolls back and no fresh presence is granted. |
| Concurrency response | First valid redeem wins. Reuse returns `token_consumed`; expired token returns `token_expired`. |
| Test requirement | Concurrent redemption of same token has one winner and no duplicate customer sessions for the same browser context. |

### Cart Mutation

| Field | Decision |
| --- | --- |
| Apps | CustomerApp |
| Owner modules | Customer Ordering, Menu Catalog |
| Public command/API | `customer_ordering.add_or_update_cart_item`, `customer_ordering.remove_cart_item` |
| Idempotency | `clientCartItemId` upsert/removal semantics; no HTTP `Idempotency-Key` in the current release. |
| Lock order | Lock CustomerOrderingSession/current active cart; lock target cart item by stable `clientCartItemId` when present. |
| Transaction boundary | Validate product/variant/modifiers server-side and upsert/remove cart item in one transaction. |
| Rollback | Failed validation does not change cart. |
| Concurrency response | Concurrent writes to the same `clientCartItemId` serialize; latest accepted write returns active cart/version. |
| Test requirement | Duplicate add/update with same client item key does not create duplicate cart rows. Invalid product leaves cart unchanged. |

### Order Submit

| Field | Decision |
| --- | --- |
| Apps | CustomerApp |
| Owner modules | Customer Ordering, Table Presence, Menu Catalog, Table Session and Billing, Preparation, Audit |
| Public command/API | `customer_ordering.submit_order`, `POST /api/customer/orders` |
| Idempotency | Required. Scope by tenant + CustomerOrderingSession + route + idempotency key. |
| Lock order | Reserve `order_submit_idempotency`; lock CustomerOrderingSession/cart; validate fresh presence; lock or create active TableSession; lock/create Check; lock selected cart items in deterministic order. |
| Transaction boundary | Idempotency reservation, cart validation, active session/check open, Order, OrderItems, snapshots, PreparationItems, audit, and submitted-cart close commit together. |
| Rollback | Failure preserves active cart and exposes no partial order, order items, check, queue items, or audit event. |
| Concurrency response | Same key/request returns original order. Same key/different request returns `idempotency_conflict` or `cart_changed_conflict`. Concurrent first order relies on unique active TableSession; loser loads existing open session. Closed/stale context returns `closed_table_session` or `fresh_presence_required` as appropriate. |
| Test requirement | Duplicate submit, same-key conflict, concurrent first order, product unavailable at submit, transaction failure after queue creation, and close-session race. |

### Preparation Queue Creation

| Field | Decision |
| --- | --- |
| Apps | Internal during CustomerApp order submit |
| Owner modules | Preparation |
| Public command/API | `preparation.create_queue_item` internal |
| Idempotency | Unique `preparation_items.order_item_id` inside the order transaction. |
| Lock order | Runs after OrderItem creation inside the order submit transaction. |
| Transaction boundary | Queue item creation is part of order submit; it must not commit without the OrderItem. |
| Rollback | Order submit rollback removes queue item creation. |
| Concurrency response | Duplicate queue insert for same OrderItem is rejected by unique constraint and treated as `already_routed` only in recovery/internal contexts. |
| Test requirement | Order replay does not create duplicate PreparationItems. |

### Preparation Status Transition

| Field | Decision |
| --- | --- |
| Apps | StationStaffApp |
| Owner modules | Preparation, Staff Access, Audit |
| Public command/API | `preparation.start_preparing`, `preparation.mark_ready`, `preparation.report_cannot_prepare` |
| Idempotency | State-guarded by current status; no required `Idempotency-Key` in the current release. |
| Lock order | Validate station assignment, then lock `preparation_items` row. |
| Transaction boundary | Status update and PreparationTransition append commit together. Cannot-prepare reason and audit/event commit with the transition. |
| Rollback | Failed transition leaves previous status and no transition row. |
| Concurrency response | Competing transitions serialize on the item row. Stale transition returns `invalid_preparation_transition`. |
| Test requirement | Two staff actions on one item yield one accepted transition and one stale/invalid response. Cannot-prepare requires reason. |

### Single-Item Service Delivery Transition

| Field | Decision |
| --- | --- |
| Apps | ServiceStaffApp |
| Owner modules | Service Delivery, Preparation, Venue Layout, Staff Access, Audit |
| Public command/API | `service_delivery.mark_picked_up`, `service_delivery.mark_delivered` |
| Idempotency | State-guarded by DeliveryState lifecycle; no required `Idempotency-Key` for single-item transition. |
| Lock order | Validate service tracking and hall scope; lock `preparation_items`; lock or create `delivery_states` for the OrderItem. |
| Transaction boundary | DeliveryState create/update and DeliveryTransition append commit together. |
| Rollback | Failed transition leaves DeliveryState and transition history unchanged. |
| Concurrency response | Concurrent delivery actions serialize on DeliveryState. Compatible repeated delivered may return current delivered state; invalid stale transition returns `invalid_delivery_transition`. |
| Test requirement | Ready-to-delivered direct path, picked-up-to-delivered path, concurrent delivered clicks, unauthorized hall, and tracking disabled. |

### Bulk Service Delivery

| Field | Decision |
| --- | --- |
| Apps | ServiceStaffApp |
| Owner modules | Service Delivery, Preparation, Venue Layout, Staff Access, Audit |
| Public command/API | `service_delivery.bulk_mark_delivered`, `POST /api/service-staff/items/bulk-deliver` |
| Idempotency | Required. Scope by tenant + actor + route + idempotency key. |
| Lock order | Reserve `delivery_bulk_idempotency`; validate same table; lock target PreparationItems/DeliveryStates in sorted OrderItem ID order. |
| Transaction boundary | All target state checks, DeliveryState creates/updates, DeliveryTransition rows, audit, and idempotency completion commit together. |
| Rollback | Any invalid selected item rolls back the whole bulk command; no partial delivery. |
| Concurrency response | Same key/request returns original BulkDeliveryResult. Same key/different request returns `idempotency_conflict`. Mixed tables return `bulk_mixed_table`; invalid item returns `bulk_item_invalid`. |
| Test requirement | Same-table success, mixed-table rejection, one invalid item rollback, duplicate replay, same key/different item set conflict. |

### Payment Record

| Field | Decision |
| --- | --- |
| Apps | CashierApp |
| Owner modules | Payments, Table Session and Billing, Staff Access, Audit |
| Public command/API | `payments.record_payment`, `POST /api/cashier/checks/{checkId}/payments` |
| Idempotency | Required. Scope by tenant + Check + route + idempotency key. |
| Lock order | Reserve `payment_idempotency`; lock Check; recompute remaining balance from source records and non-voided payments. |
| Transaction boundary | Payment insert, idempotency completion, audit, and optional bill read model update commit together. |
| Rollback | Failed payment leaves no Payment row and does not reduce remaining balance. |
| Concurrency response | Same key/request returns original payment. Same key/different request returns `idempotency_conflict`. Concurrent payments serialize on Check; overpay after recomputation returns `overpayment_not_allowed`. Closed check returns `check_closed`. |
| Test requirement | Duplicate payment submit, concurrent partial payments, overpayment race, payment against closed Check. |

### Payment Void

| Field | Decision |
| --- | --- |
| Apps | CashierApp |
| Owner modules | Payments, Table Session and Billing, Staff Access, Audit |
| Public command/API | `payments.void_payment`, `POST /api/cashier/payments/{paymentId}/void` |
| Idempotency | Required. Scope by tenant + Payment + route + idempotency key. |
| Lock order | Reserve `payment_void_idempotency`; lock Check; lock Payment; append required CashierCorrection; set immutable void fields. |
| Transaction boundary | Payment void fields, required correction, audit, idempotency completion, and optional bill read model update commit together. |
| Rollback | Failed void leaves Payment recorded and creates no payment-void correction. |
| Concurrency response | Same key/request returns original void result. Same key/different request returns `idempotency_conflict`. Already voided payment returns current compatible result only through idempotency; otherwise `payment_void_not_allowed`. Closed Check returns `check_closed`. |
| Test requirement | Duplicate void replay, same key/different reason conflict, concurrent void attempts, closed Check rejection. |

### Cashier Correction

| Field | Decision |
| --- | --- |
| Apps | CashierApp |
| Owner modules | Table Session and Billing, Payments, Preparation, Staff Access, Audit |
| Public command/API | `table_session_billing.record_cashier_correction`, `POST /api/cashier/checks/{checkId}/corrections` |
| Idempotency | Required. Scope by tenant + Check + route + idempotency key. |
| Lock order | Reserve `cashier_correction_idempotency`; lock Check; lock target record in deterministic order. For item void, lock OrderItem then PreparationItem; Check lock prevents concurrent payment recording while eligibility is checked. |
| Transaction boundary | Correction record, target mutation when allowed, audit, idempotency completion, and optional bill read model update commit together. |
| Rollback | Failed correction creates no correction row and does not mutate the target. |
| Concurrency response | Same key/request returns original correction. Same key/different request returns `idempotency_conflict`. Ineligible target returns `correction_not_allowed`; closed Check returns `check_closed`; missing reason returns `reason_required`. |
| Test requirement | Duplicate correction replay, item void after payment race, item void after invalid preparation state, missing reason, note-only correction. |

### Session Close

| Field | Decision |
| --- | --- |
| Apps | CashierApp |
| Owner modules | Table Session and Billing, Payments, Customer Ordering, Audit |
| Public command/API | `table_session_billing.close_session`, `POST /api/cashier/table-sessions/{tableSessionId}/close` |
| Idempotency | State-guarded by TableSession/Check status and unique SessionClosure; no required `Idempotency-Key` in the current release. |
| Lock order | Lock TableSession, then Check. Check lock blocks concurrent payment/correction while balance is recomputed. |
| Transaction boundary | Recompute balance, insert SessionClosure, close Check, close TableSession, audit, and optional read model update commit together. |
| Rollback | Failed close leaves TableSession and Check open. |
| Concurrency response | Duplicate close returns already-closed state or stale command without mutation. Remaining balance returns `remaining_balance_not_zero`. Concurrent order submit must not attach to a closed session. Concurrent payment waits on Check and is evaluated after close state. |
| Test requirement | Full-payment close, duplicate close, concurrent payment/close, concurrent order/close, nonzero balance rejection. |

### First Password Setup With OTP

| Field | Decision |
| --- | --- |
| Apps | TenantApp, CashierApp, staff apps |
| Owner modules | Identity and Access, OTP Messaging, Reliable Side Effects, Audit |
| Public command/API | `identity_access.begin_first_password_setup`, `otp_messaging.verify_otp`, `identity_access.complete_first_password_setup` |
| Idempotency | State-guarded by setup token, credential bootstrap flag, OTP challenge state, and OTP attempt accounting. |
| Lock order | For begin: lock user/credential setup state before creating challenge. For verify: lock OTP challenge. For complete: lock credential/setup token, then consume verified OTP proof when required. |
| Transaction boundary | Challenge creation records database state only; SMS delivery is an outbox/side-effect after commit. OTP verify locks challenge and appends attempt. Password completion replaces credential hash and clears bootstrap state in one transaction. |
| Rollback | SMS failure does not rollback challenge creation. Failed password completion does not clear bootstrap flag. Failed OTP verify appends failed attempt but does not verify challenge. |
| Concurrency response | Repeated successful OTP verify is idempotent for that challenge. Excess attempts return `otp_locked`; expired challenge returns `otp_expired`; missing proof returns `otp_required`. |
| Test requirement | Tenant admin/cashier require OTP, station/service staff do not, concurrent verify attempts respect max attempts, password completion cannot run twice. |

### OTP Send

| Field | Decision |
| --- | --- |
| Apps | TenantApp, CashierApp setup surfaces |
| Owner modules | OTP Messaging, Reliable Side Effects |
| Public command/API | `otp_messaging.send_otp`, `POST /api/auth/otp-challenges/{challengeId}/send` |
| Idempotency | Send count and challenge state guarded; no required `Idempotency-Key` in the current release. |
| Lock order | Lock OTP challenge; insert `message_deliveries`; enqueue side effect with stable idempotency reference. |
| Transaction boundary | Delivery attempt record and outbox enqueue commit before provider send. |
| Rollback | If enqueue fails, no send attempt is committed. Provider failure after commit is recorded as delivery failure/retry state. |
| Concurrency response | Concurrent sends serialize on challenge and respect current release max sends. Expired/locked challenge returns `otp_expired` or `otp_locked`. |
| Test requirement | Max send limit, concurrent send limit, provider failure records redacted failure without exposing OTP code. |

### Outbox Worker Claim and Attempt

| Field | Decision |
| --- | --- |
| Apps | Worker/recovery tooling |
| Owner modules | Reliable Side Effects |
| Public command/API | `side_effects.claim_next_effect`, `record_attempt`, `mark_completed`, `mark_failed`, `recover_stale_claims` |
| Idempotency | Unique `effect_type + idempotency_ref` protects enqueue; worker claim uses row-level locking. |
| Lock order | Recover expired claimed rows first when applicable; claim next pending/failed/stale row with `select for update skip locked` or atomic status update; append attempt; update message terminal/retry status. |
| Transaction boundary | Claim transaction is short. Provider call happens outside the claim transaction. Attempt result is recorded in a separate transaction. |
| Rollback | Provider call cannot be rolled back. If worker crashes before provider call, claim lease expiry makes the message retryable. If worker crashes after provider call and before attempt record, recovery must use provider/idempotency evidence where available. |
| Concurrency response | Competing workers skip locked rows; active claims are not stolen before lease expiry; duplicate enqueue returns `duplicate_effect` or existing effect state. |
| Test requirement | Parallel workers do not process the same outbox row at the same time; expired claims are recovered; retry schedule is respected; provider payload is redacted. |

## Cross-Flow Race Requirements

| Race | Required Outcome |
| --- | --- |
| QR redeem vs token expiry | Atomic consume decides. Expired token cannot create fresh presence. |
| Order submit vs session close | TableSession lock decides. Order must not attach to a closed session. |
| Concurrent first orders at one table | Unique active TableSession ensures one open session; loser loads existing open session. |
| Payment vs close | Check lock serializes; close recomputes balance after committed payments. |
| Payment vs item void | Check lock serializes; item void after any payment is rejected in the current release. |
| Payment void vs close | Check lock serializes; closed Check cannot be voided in the current release. |
| Bulk delivery vs single delivery | DeliveryState locks and deterministic item order prevent partial or conflicting transitions. |
| Staff scope change vs staff action | Authorization must be checked at mutation time, not only at login. |
| Tenant suspension vs runtime action | Runtime commands must check tenant availability before mutation; already locked business transactions fail closed if tenant is not active. |

## Minimum Concurrency Test Matrix

| Area | Required Test |
| --- | --- |
| Provisioning | Concurrent same-subdomain create; retry failed starter; no starter rerun after success. |
| QR | Concurrent token redeem; expired token redeem; display fetch concurrent current token. |
| Ordering | Duplicate submit; same-key different cart; concurrent first order; order while close waits/commits. |
| Fulfillment | Concurrent station transitions; single delivery duplicate; bulk delivery one invalid item rollback. |
| Settlement | Concurrent payments; payment/close race; item void/payment race; duplicate correction; payment void race. |
| OTP | Concurrent verify attempts; max attempts; SMS provider failure after challenge commit. |
| Outbox | Parallel worker claim; stale claim recovery; retryable failure schedule; duplicate enqueue idempotency. |

## Implementation Notes

- Use PostgreSQL unique constraints as the final duplicate barrier; do not rely on frontend disabled buttons.
- Prefer normal PostgreSQL row locks with explicit lock order. Escalate isolation only when a documented invariant cannot be protected by locks and constraints.
- Keep side-effect payloads redacted before insertion. Raw OTP codes, raw QR tokens, raw credentials, session tokens, and provider payloads must not enter outbox or audit metadata.
- Every transaction in this catalog must have at least one integration test before the corresponding backend flow is considered complete.
