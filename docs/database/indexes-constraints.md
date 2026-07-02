# PostgreSQL Indexes and Constraints

This document defines the v1 PostgreSQL integrity layer for the schema in [schema.md](schema.md).

The rule is simple: if duplicate submits, stale permissions, wrong-tenant references, replayed QR tokens, or invalid payments can corrupt business state, the database must help prevent it. Frontend and backend guards are required, but they are not enough.

## Naming

Use explicit names so Alembic migrations and production errors are readable.

| Object | Naming Pattern | Example |
| --- | --- | --- |
| Primary key | `pk_{table}` | `pk_tenants` |
| Foreign key | `fk_{table}__{column}__{ref_table}` | `fk_orders__table_session_id__table_sessions` |
| Unique constraint/index | `uq_{table}__{columns}` | `uq_tenants__subdomain_lower` |
| Check constraint | `ck_{table}__{rule}` | `ck_payments__amount_positive` |
| Non-unique index | `ix_{table}__{columns}` | `ix_orders__tenant_table_session_submitted` |

## Baseline Rules

- Every foreign key used in joins or deletes gets an index.
- Every tenant-scoped table gets at least one leading `tenant_id` query index if it is queried outside a direct primary-key lookup.
- Partial unique indexes enforce active singleton rules.
- `ON DELETE CASCADE` is not used for business history tables.
- Historical records are preserved. Disable, revoke, close, void, or append a correction instead of deleting referenced records.
- Cross-tenant references must be prevented with composite foreign keys where simple single-column FKs would allow mismatched tenant ownership.

## Foreign Key Policy

| Relationship Type | Delete Behavior |
| --- | --- |
| Historical business records to parent aggregate | `RESTRICT` / no delete |
| Read models to owning tenant | `CASCADE` only if full tenant purge tooling exists; otherwise `RESTRICT` in v1 |
| Setup records referenced by history | `RESTRICT`; use `enabled = false` instead |
| Append-only audit/outbox records | `RESTRICT` |
| Cart/cart item records | `RESTRICT` in v1, retention purge can be introduced later |

V1 should not implement tenant hard-delete. Tenant deletion is out of scope until retention and legal rules exist.

## Primary Keys

All tables in [schema.md](schema.md) use `uuid` primary keys except one-to-one tables where the parent key is the primary key:

| Table | Primary Key |
| --- | --- |
| `tenant_operational_settings` | `tenant_id` |
| `tenant_health` | `tenant_id` |
| `credentials` | `user_id` |
| `totp_factors` | `user_id` |
| `staff_profiles` | `user_id` |

## Required Unique Constraints

### Platform

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `tenants` | unique index on `lower(subdomain)` | Prevent duplicate tenant domains, case-insensitive. |
| `tenant_operational_settings` | primary key `tenant_id` | One settings row per tenant. |
| `tenant_health` | primary key `tenant_id` | One platform health summary per tenant. |
| `starter_template_applications` | unique `(tenant_id, template_key, template_version)` | Prevent starter data reruns. |

### Access

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `users` | unique `(tenant_id, lower(username))` where `tenant_id is not null` | Prevent duplicate tenant usernames. |
| `users` | unique `lower(username)` where `tenant_id is null` | Prevent duplicate platform usernames. |
| `credentials` | primary key `user_id` | One credential record per user. |
| `login_sessions` | unique `session_token_hash` | Prevent ambiguous session authentication. |
| `platform_role_assignments` | unique `role` where `role = 'platform_owner' and status = 'active'` | Enforce single active Platform Owner in v1. |
| `totp_factors` | primary key `user_id` | One active TOTP factor record per user in v1. |
| `staff_profiles` | primary key `user_id` | One staff profile per user. |
| `staff_role_assignments` | unique `(tenant_id, user_id, role)` where `status = 'active'` | Prevent duplicate active role grant. |
| `staff_station_assignments` | unique `(tenant_id, user_id, station_id)` where `status = 'active'` | Prevent duplicate active station assignment. |
| `staff_hall_assignments` | unique `(tenant_id, user_id, hall_id)` where `status = 'active'` | Prevent duplicate active hall assignment. |

### Tenant Setup

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `halls` | unique `(tenant_id, lower(name))` | Prevent duplicate hall names inside tenant. |
| `halls` | unique `(tenant_id, display_order)` | Keep hall ordering deterministic. |
| `venue_tables` | unique `(tenant_id, hall_id, lower(name))` | Prevent duplicate table labels inside hall. |
| `venue_tables` | unique `(tenant_id, hall_id, display_order)` | Keep table grid ordering deterministic. |
| `stations` | unique `(tenant_id, lower(name))` | Prevent duplicate station names. |
| `stations` | unique `(tenant_id, display_order)` | Keep station ordering deterministic. |
| `menu_categories` | unique `(tenant_id, lower(name))` | Prevent duplicate customer category names. |
| `menu_categories` | unique `(tenant_id, display_order)` | Keep category ordering deterministic. |
| `product_services` | unique `(tenant_id, category_id, lower(name))` | Prevent duplicate product names inside category. |
| `product_variants` | unique `(tenant_id, product_service_id, lower(name))` | Prevent duplicate variant names inside product. |
| `product_variants` | unique `(tenant_id, product_service_id)` where `is_default = true` | Enforce one default variant per product. |
| `modifier_groups` | unique `(tenant_id, product_service_id, lower(name))` | Prevent duplicate modifier groups. |
| `modifier_options` | unique `(tenant_id, modifier_group_id, lower(name))` | Prevent duplicate modifier options. |

At least one enabled `product_variants` row for an enabled `product_services` row cannot be expressed as a simple check constraint. Enforce it in the service transaction and cover it with integration tests. A deferred trigger is acceptable later if the invariant becomes hard to maintain.

### Table Display and Presence

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `table_display_claims` | unique `claim_hash` | Prevent claim collision/replay ambiguity. |
| `table_display_credentials` | unique `credential_hash` | Prevent ambiguous display authentication. |
| `table_display_credentials` | unique `(tenant_id, table_id)` where `status = 'active'` | One active ESP32 table display credential per table. |
| `table_access_tokens` | unique `token_hash` | Prevent QR token collision/replay ambiguity. |

Only one live unconsumed QR token per display should be enforced by the token issuance transaction with a table/display lock. Do not use a partial index involving `now()`, because PostgreSQL indexes cannot safely depend on volatile time expressions.

### Customer Ordering and Settlement

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `customer_ordering_sessions` | unique `cookie_token_hash` | Prevent ambiguous anonymous browser session authentication. |
| `customer_carts` | unique `(tenant_id, customer_ordering_session_id)` where `status = 'active'` | One active cart per customer ordering session. |
| `customer_cart_items` | unique `(tenant_id, cart_id, client_cart_item_id)` | Make cart item updates idempotent from the browser. |
| `order_submit_idempotency` | unique `(tenant_id, customer_ordering_session_id, idempotency_key)` | Prevent duplicate order submit. |
| `table_sessions` | unique `(tenant_id, table_id)` where `status = 'open'` | One active table session per table. |
| `checks` | unique `table_session_id` | Exactly one Check/Adisyon per TableSession in v1. |
| `session_closures` | unique `table_session_id` | Prevent duplicate close records. |
| `preparation_items` | unique `(tenant_id, order_item_id)` | One station queue item per tenant order item. |
| `delivery_states` | unique `(tenant_id, order_item_id)` | One delivery state per tenant order item. |
| `delivery_bulk_idempotency` | unique `(tenant_id, actor_user_id, idempotency_key)` | Prevent duplicate same-actor bulk delivery commands. |
| `payment_idempotency` | unique `(tenant_id, check_id, idempotency_key)` | Prevent duplicate payment recording. |
| `payment_void_idempotency` | unique `(tenant_id, payment_id, idempotency_key)` | Prevent duplicate payment void/correction commands. |
| `cashier_correction_idempotency` | unique `(tenant_id, check_id, idempotency_key)` | Prevent duplicate cashier correction commands. |

### OTP and Governance

| Table | Constraint / Index | Purpose |
| --- | --- | --- |
| `otp_attempts` | unique `(tenant_id, otp_challenge_id, attempt_no)` | Preserve tenant-scoped monotonic attempt accounting. |
| `message_deliveries` | unique `(tenant_id, otp_challenge_id, delivery_no)` | Preserve tenant-scoped SMS send attempt accounting. |
| `outbox_messages` | unique `(effect_type, idempotency_ref)` | Prevent duplicate external side effects. |
| `external_effect_attempts` | unique `(outbox_message_id, attempt_no)` | Preserve retry history. |

## Required Check Constraints

### Status and Enum Checks

Every value set listed in [schema.md](schema.md#domain-value-sets) must have a named check constraint on the relevant column.

Examples:

```sql
constraint ck_tenants__status
  check (status in ('provisioning', 'active', 'suspended', 'provisioning_failed'))
```

```sql
constraint ck_preparation_items__status
  check (status in ('pending', 'preparing', 'ready', 'cannot_prepare'))
```

### Numeric Checks

| Table | Check | Purpose |
| --- | --- | --- |
| `tenants` | `capacity is null or capacity > 0` | Prevent invalid capacity values. |
| `product_variants` | `price_minor >= 0` | Allow free items if explicitly configured, reject negative prices. |
| `modifier_options` | `price_delta_minor >= 0` in v1 | Paid add-ons only in v1; negative discounts are out of scope. |
| `customer_cart_items` | `quantity > 0` | Prevent invalid cart lines. |
| `order_items` | `quantity > 0` | Prevent invalid billable lines. |
| `payments` | `amount_minor > 0` | Prevent invalid payments. |
| `modifier_groups` | `min_selections >= 0 and max_selections >= min_selections` | Preserve modifier selection rules. |

### Lifecycle and Nullability Checks

| Table | Check | Purpose |
| --- | --- | --- |
| `tenants` | `provisioning_error is null or status = 'provisioning_failed'` | Avoid stale error text on active tenants. |
| `tenant_lifecycle_events` | `previous_status is distinct from next_status` where previous exists | Prevent no-op lifecycle history. |
| `platform_role_assignments` | referenced user must have `tenant_id is null` | Requires service validation or trigger; cannot be expressed with simple check. |
| `staff_profiles` | referenced user must have same `tenant_id` | Enforce with composite FK or service validation. |
| `availability_overrides` | `expires_at is null or starts_at is null or expires_at > starts_at` | Prevent invalid windows. |
| `availability_overrides` | product variant must belong to product when `product_variant_id` is present | Enforce with composite FK. |
| `table_display_claims` | `consumed_at is null or consumed_at <= expires_at` | Preserve one-time claim lifecycle. |
| `table_display_credentials` | `(status = 'active' and revoked_at is null) or (status = 'revoked' and revoked_at is not null)` | Keep credential lifecycle coherent. |
| `table_access_tokens` | `consumed_at is null or consumed_at <= expires_at` | Preserve token lifecycle. |
| `customer_ordering_sessions` | `presence_valid_until <= expires_at` | Presence cannot outlive session. |
| `order_submit_idempotency` | completed rows require `order_id` and `completed_at` | Prevent ambiguous idempotency results. |
| `table_sessions` | closed rows require `closed_at`; open rows require `closed_at is null` | Preserve session lifecycle. |
| `checks` | closed rows require `closed_at`; open rows require `closed_at is null` | Preserve Check lifecycle. |
| `order_items` | void fields must be all present or all null | Prevent half-voided line items. |
| `preparation_items` | `cannot_prepare_reason` required only for `cannot_prepare` | Preserve exception semantics. |
| `preparation_transitions` | `reason` required when `to_status = 'cannot_prepare'` | Preserve exception auditability. |
| `delivery_transitions` | `from_status is distinct from to_status` where previous exists | Prevent no-op delivery transitions. |
| `delivery_bulk_idempotency` | completed rows require `completed_at` and `delivered_order_item_ids` | Prevent ambiguous bulk delivery replay results. |
| `payments` | void fields must be all present or all null | Prevent half-voided payments. |
| `payments` | `status = 'voided'` iff void fields are present | Preserve payment lifecycle. |
| `payment_idempotency` | completed rows require `payment_id` and `completed_at` | Prevent ambiguous payment replay results. |
| `payment_void_idempotency` | completed rows require `completed_at` | Prevent ambiguous payment-void replay results. |
| `price_adjustments` | `reason` required when `type = 'correction'` | Preserve correction auditability. |
| `cashier_corrections` | `reason <> ''` | Corrections always need a reason. |
| `cashier_correction_idempotency` | completed rows require `cashier_correction_id` and `completed_at` | Prevent ambiguous correction replay results. |
| `otp_challenges` | `verified_at is null or verified_at <= expires_at` | Prevent success after expiry. |
| `otp_attempts` | `attempt_no between 1 and 5` | Enforce v1 verification attempt limit at the database boundary. |
| `message_deliveries` | `delivery_no between 1 and 3` | Enforce v1 SMS send attempt limit at the database boundary. |
| `message_deliveries` | queued rows have no completion/error; sent/failed rows require completion; failed rows require redacted error summary | Preserve provider delivery lifecycle without storing sensitive payloads. |
| `outbox_messages` | claimed rows require `claimed_by`, `claimed_at`, and `claim_expires_at`; non-claimed rows clear claim lease fields | Preserve recoverable worker claim lifecycle. |
| `outbox_messages` | `claim_expires_at is null or claim_expires_at > claimed_at` | Prevent immediately expired or invalid worker leases. |
| `outbox_messages` | completed rows require `completed_at`; non-completed rows clear it | Prevent ambiguous outbox terminal state. |
| `outbox_messages` | `payload_ref` must be a JSON object | Preserve structured redacted side-effect payload references. |
| `external_effect_attempts` | failed/timeout attempts require `completed_at` and redacted `result_summary`; success requires `completed_at` | Preserve provider attempt evidence without raw sensitive payloads. |
| `audit_events` | `metadata` must be a JSON object and contain no raw secrets | DB enforces structure; service sanitizer and tests enforce semantic secrecy. |

## Composite Foreign Keys for Tenant Integrity

Single-column UUID FKs prove the target row exists, but they do not prove both records belong to the same tenant. For tenant-owned relationships, add composite uniqueness on `(tenant_id, id)` to referenced tables and use composite FKs from children.

Required examples:

| Child Table | Composite FK | Purpose |
| --- | --- | --- |
| `tenant_operational_settings` | `(tenant_id)` -> `tenants(id)` | Settings cannot exist without tenant. |
| `tenant_health` | `(tenant_id)` -> `tenants(id)` | Health summary cannot exist without tenant. |
| `starter_template_applications` | `(tenant_id)` -> `tenants(id)` | Starter application proof cannot exist without tenant. |
| `staff_profiles` | `(tenant_id, user_id)` -> `users(tenant_id, id)` | Staff profile cannot point to another tenant's user. |
| `staff_role_assignments` | `(tenant_id, user_id)` -> `users(tenant_id, id)` | Staff role cannot point to another tenant's user. |
| `staff_station_assignments` | `(tenant_id, user_id)` -> `users(tenant_id, id)` | Station assignment user cannot cross tenant. |
| `staff_station_assignments` | `(tenant_id, station_id)` -> `stations(tenant_id, id)` | Station assignment target cannot cross tenant. |
| `staff_hall_assignments` | `(tenant_id, user_id)` -> `users(tenant_id, id)` | Hall assignment user cannot cross tenant. |
| `staff_hall_assignments` | `(tenant_id, hall_id)` -> `halls(tenant_id, id)` | Hall assignment target cannot cross tenant. |
| `venue_tables` | `(tenant_id, hall_id)` -> `halls(tenant_id, id)` | Table cannot point to another tenant's hall. |
| `product_services` | `(tenant_id, category_id)` -> `menu_categories(tenant_id, id)` | Product cannot point to another tenant's category. |
| `product_services` | `(tenant_id, station_id)` -> `stations(tenant_id, id)` | Product cannot route to another tenant's station. |
| `product_variants` | `(tenant_id, product_service_id)` -> `product_services(tenant_id, id)` | Variant cannot cross tenant. |
| `availability_overrides` | `(tenant_id, product_service_id)` -> `product_services(tenant_id, id)` | Override target cannot cross tenant. |
| `availability_overrides` | `(tenant_id, product_service_id, product_variant_id)` -> `product_variants(tenant_id, product_service_id, id)` | Variant override must belong to the product. |
| `availability_overrides` | `(tenant_id, created_by_user_id)` -> `users(tenant_id, id)` | Availability actor cannot cross tenant. |
| `modifier_groups` | `(tenant_id, product_service_id)` -> `product_services(tenant_id, id)` | Modifier group cannot cross tenant. |
| `modifier_options` | `(tenant_id, modifier_group_id)` -> `modifier_groups(tenant_id, id)` | Option cannot cross tenant. |
| `table_display_claims` | `(tenant_id, table_id)` -> `venue_tables(tenant_id, id)` | Claim cannot provision another tenant's table. |
| `table_display_claims` | `(tenant_id, created_by_user_id)` -> `users(tenant_id, id)` | Claim creator cannot cross tenant. |
| `table_display_credentials` | `(tenant_id, table_id)` -> `venue_tables(tenant_id, id)` | Credential cannot authenticate another tenant's table. |
| `table_access_tokens` | `(tenant_id, table_id)` -> `venue_tables(tenant_id, id)` | QR token cannot target another tenant's table. |
| `customer_ordering_sessions` | `(tenant_id, table_id)` -> `venue_tables(tenant_id, id)` | Customer session cannot target another tenant's table. |
| `customer_carts` | `(tenant_id, customer_ordering_session_id)` -> `customer_ordering_sessions(tenant_id, id)` | Cart cannot cross tenant. |
| `customer_cart_items` | `(tenant_id, cart_id)` -> `customer_carts(tenant_id, id)` | Cart item cannot cross tenant. |
| `customer_cart_items` | `(tenant_id, product_service_id)` -> `product_services(tenant_id, id)` | Cart product cannot cross tenant. |
| `customer_cart_items` | `(tenant_id, product_service_id, product_variant_id)` -> `product_variants(tenant_id, product_service_id, id)` | Cart variant must belong to selected product. |
| `order_submit_idempotency` | `(tenant_id, customer_ordering_session_id)` -> `customer_ordering_sessions(tenant_id, id)` | Idempotency record cannot cross tenant/session. |
| `order_submit_idempotency` | `(tenant_id, order_id)` -> `orders(tenant_id, id)` when present | Idempotency result cannot point to another tenant's order. |
| `orders` | `(tenant_id, customer_ordering_session_id)` -> `customer_ordering_sessions(tenant_id, id)` | Order cannot cross tenant/session. |
| `orders` | `(tenant_id, table_session_id)` -> `table_sessions(tenant_id, id)` | Order cannot cross tenant/table session. |
| `order_items` | `(tenant_id, order_id)` -> `orders(tenant_id, id)` | Order item cannot cross tenant. |
| `order_items` | `(tenant_id, product_service_id)` -> `product_services(tenant_id, id)` | Order snapshot source product cannot cross tenant. |
| `order_items` | `(tenant_id, product_service_id, product_variant_id)` -> `product_variants(tenant_id, product_service_id, id)` | Order snapshot source variant must belong to product. |
| `order_items` | `(tenant_id, station_id)` -> `stations(tenant_id, id)` | Routing snapshot cannot cross tenant. |
| `preparation_items` | `(tenant_id, order_item_id, station_id)` -> `order_items(tenant_id, id, station_id)` | Queue item cannot cross tenant or drift from the OrderItem routing snapshot. |
| `preparation_items` | `(tenant_id, station_id)` -> `stations(tenant_id, id)` | Queue station cannot cross tenant. |
| `preparation_transitions` | `(tenant_id, preparation_item_id)` -> `preparation_items(tenant_id, id)` | Preparation transition cannot cross tenant. |
| `preparation_transitions` | `(tenant_id, actor_user_id)` -> `users(tenant_id, id)` | Preparation actor cannot cross tenant. |
| `delivery_states` | `(tenant_id, order_item_id)` -> `order_items(tenant_id, id)` | Delivery state cannot cross tenant. |
| `delivery_transitions` | `(tenant_id, delivery_state_id, order_item_id)` -> `delivery_states(tenant_id, id, order_item_id)` | Delivery transition cannot cross tenant or drift from its DeliveryState item. |
| `delivery_transitions` | `(tenant_id, actor_user_id)` -> `users(tenant_id, id)` | Delivery actor cannot cross tenant. |
| `delivery_bulk_idempotency` | `(tenant_id, actor_user_id)` -> `users(tenant_id, id)` | Bulk delivery actor cannot cross tenant. |
| `delivery_bulk_idempotency` | `(tenant_id, table_id)` -> `venue_tables(tenant_id, id)` | Bulk delivery target table cannot cross tenant. |
| `checks` | `(tenant_id, table_session_id)` -> `table_sessions(tenant_id, id)` | Check cannot cross tenant. |
| `price_adjustments` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Price adjustment cannot cross tenant. |
| `price_adjustments` | `(tenant_id, order_item_id)` -> `order_items(tenant_id, id)` when present | Item adjustment target cannot cross tenant. |
| `price_adjustments` | `(tenant_id, created_by_user_id)` -> `users(tenant_id, id)` | Adjustment actor cannot cross tenant. |
| `session_closures` | `(tenant_id, table_session_id)` -> `table_sessions(tenant_id, id)` | Closure cannot cross tenant/session. |
| `session_closures` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Closure Check cannot cross tenant. |
| `session_closures` | `(tenant_id, cashier_user_id)` -> `users(tenant_id, id)` | Closing cashier cannot cross tenant. |
| `payments` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Payment cannot cross tenant. |
| `payments` | `(tenant_id, cashier_user_id)` -> `users(tenant_id, id)` | Payment cashier cannot cross tenant. |
| `payments` | `(tenant_id, voided_by_user_id)` -> `users(tenant_id, id)` when present | Void actor cannot cross tenant. |
| `payment_idempotency` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Payment idempotency cannot cross tenant/check. |
| `payment_idempotency` | `(tenant_id, payment_id)` -> `payments(tenant_id, id)` when present | Payment idempotency result cannot point to another tenant's payment. |
| `payment_void_idempotency` | `(tenant_id, payment_id)` -> `payments(tenant_id, id)` | Payment void idempotency cannot cross tenant/payment. |
| `cashier_corrections` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Correction cannot cross tenant. |
| `cashier_corrections` | `(tenant_id, created_by_user_id)` -> `users(tenant_id, id)` | Correction actor cannot cross tenant. |
| `cashier_correction_idempotency` | `(tenant_id, check_id)` -> `checks(tenant_id, id)` | Correction idempotency cannot cross tenant/check. |
| `cashier_correction_idempotency` | `(tenant_id, cashier_correction_id)` -> `cashier_corrections(tenant_id, id)` when present | Correction idempotency result cannot point to another tenant's correction. |
| `otp_challenges` | `(tenant_id, user_id)` -> `users(tenant_id, id)` | OTP challenge cannot target another tenant's user. |
| `otp_attempts` | `(tenant_id, otp_challenge_id)` -> `otp_challenges(tenant_id, id)` | OTP attempt cannot cross tenant. |
| `message_deliveries` | `(tenant_id, otp_challenge_id)` -> `otp_challenges(tenant_id, id)` | OTP delivery cannot cross tenant. |

## Query Indexes by App

### PlatformApp

| Query | Index |
| --- | --- |
| Resolve tenant by subdomain | `ix_tenants__subdomain_lower` unique index |
| List active tenants | `ix_tenants__status_created` on `(status, created_at desc)` |
| Tenant health list | `ix_tenant_health__updated` on `(updated_at desc)` |
| Tenant lifecycle timeline | `ix_tenant_lifecycle_events__tenant_created` on `(tenant_id, created_at desc)` |

### TenantApp

| Query | Index |
| --- | --- |
| Hall list | `ix_halls__tenant_display` on `(tenant_id, display_order)` |
| Tables by hall | `ix_venue_tables__tenant_hall_display` on `(tenant_id, hall_id, display_order)` |
| Station list | `ix_stations__tenant_display` on `(tenant_id, display_order)` |
| Menu categories | `ix_menu_categories__tenant_display` on `(tenant_id, display_order)` |
| Products by category | `ix_product_services__tenant_category_display` on `(tenant_id, category_id, enabled, name)` or display order if added |
| Variants by product | `ix_product_variants__tenant_product_display` on `(tenant_id, product_service_id, display_order)` |
| Active staff roles | `ix_staff_role_assignments__tenant_user_active` on `(tenant_id, user_id)` where `status = 'active'` |

### CustomerApp

| Query | Index |
| --- | --- |
| Redeem QR token | unique `ix_table_access_tokens__token_hash` |
| Resolve customer session cookie | unique `ix_customer_ordering_sessions__cookie_token_hash` |
| Active menu | `ix_product_services__tenant_enabled_category` and `ix_product_variants__tenant_product_enabled` |
| Current cart | unique active cart index |
| Cart items | `ix_customer_cart_items__tenant_cart` on `(tenant_id, cart_id)` |
| My orders | `ix_orders__tenant_customer_session_submitted` on `(tenant_id, customer_ordering_session_id, submitted_at desc)` |
| Table orders | `ix_orders__tenant_table_session_submitted` on `(tenant_id, table_session_id, submitted_at desc)` |
| Order items | `ix_order_items__tenant_order` on `(tenant_id, order_id)` |

### StationStaffApp

| Query | Index |
| --- | --- |
| Assigned stations | `ix_staff_station_assignments__tenant_user_active` on `(tenant_id, user_id)` where `status = 'active'` |
| Station queue | `ix_preparation_items__tenant_station_status_updated` on `(tenant_id, station_id, status, updated_at desc)` |
| Item transition history | `ix_preparation_transitions__tenant_item_created` on `(tenant_id, preparation_item_id, created_at)` |

### ServiceStaffApp

| Query | Index |
| --- | --- |
| Assigned halls | `ix_staff_hall_assignments__tenant_user_active` on `(tenant_id, user_id)` where `status = 'active'` |
| Ready items | `ix_preparation_items__tenant_status_updated` on `(tenant_id, status, updated_at)` |
| Delivery state by item | unique `delivery_states(tenant_id, order_item_id)` |
| Delivery workload/history | `ix_delivery_transitions__tenant_item_created` on `(tenant_id, order_item_id, created_at desc)` |
| Bulk delivery idempotency replay | unique `delivery_bulk_idempotency(tenant_id, actor_user_id, idempotency_key)` |

Service queue joins require indexed path:

- `preparation_items.order_item_id`
- `order_items.order_id`
- `orders.table_session_id`
- `table_sessions.table_id`
- `venue_tables.hall_id`

### CashierApp

| Query | Index |
| --- | --- |
| Open sessions by table | unique active table session index |
| Open sessions by tenant | `ix_table_sessions__tenant_status_opened` on `(tenant_id, status, opened_at desc)` |
| Check by session | unique `checks(table_session_id)` |
| Payments by check | `ix_payments__tenant_check_received` on `(tenant_id, check_id, received_at desc)` |
| Payment history by business day | `ix_payments__tenant_received` on `(tenant_id, received_at desc)` |
| Corrections by check | `ix_cashier_corrections__tenant_check_created` on `(tenant_id, check_id, created_at desc)` |
| Closure by session | unique `session_closures(table_session_id)` |

### Governance and Workers

| Query | Index |
| --- | --- |
| Audit by tenant/time | `ix_audit_events__tenant_created` on `(tenant_id, created_at desc)` |
| Audit by target | `ix_audit_events__target` on `(target_type, target_id, created_at desc)` |
| Audit by action/time | `ix_audit_events__action_created` on `(action, created_at desc)` |
| Outbox claim next pending/stale | `ix_outbox_messages__status_next_attempt` on `(status, next_attempt_at, claim_expires_at, created_at)` where `status in ('pending', 'failed', 'claimed')` |
| Outbox by aggregate | `ix_outbox_messages__aggregate` on `(aggregate_type, aggregate_id)` |
| Effect attempts by message | unique `(outbox_message_id, attempt_no)` plus `ix_external_effect_attempts__message_started` |
| OTP challenge lookup | `ix_otp_challenges__tenant_user_purpose_created` on `(tenant_id, user_id, purpose, created_at desc)` |
| OTP attempt history | `ix_otp_attempts__tenant_challenge_created` on `(tenant_id, otp_challenge_id, created_at desc)` |
| OTP delivery history | `ix_message_deliveries__tenant_challenge_created` on `(tenant_id, otp_challenge_id, created_at desc)` |

## Locking and Transaction Requirements

These are database behavior requirements, not API suggestions.

| Operation | Required Database Protection |
| --- | --- |
| Tenant creation | Use the phased provisioning flow in [seed-provisioning.md](seed-provisioning.md): reserve tenant first, then apply required records in one locked transaction, then mark failure separately if needed. |
| Starter template retry | Lock tenant and starter application rows with `select for update`; never apply successful template twice. |
| Display claim consumption | Atomic update `where consumed_at is null and expires_at > now()`; only winner receives credential. |
| Display credential rotation | Lock tenant/table credential rows; revoke old active credential before inserting active replacement. |
| QR token redemption | Atomic update `where consumed_at is null and expires_at > now()`; only winner refreshes presence. |
| Order submit | Reserve idempotency row first, then lock active cart and active/open table session path. Duplicate key returns original result. |
| Open table session | Rely on partial unique open-session index and handle conflict by loading existing open session. |
| Station status transition | Lock `preparation_items` row; validate allowed transition from current state. |
| Delivery transition | Lock `delivery_states` or create first state with unique `order_item_id`; validate hall scope before mutation. |
| Bulk delivery | Reserve idempotency row, lock all target order/preparation/delivery rows in deterministic order, validate same table and hall scope, then transition all items atomically. |
| Payment record | Reserve payment idempotency row, lock Check, compute remaining balance in transaction, reject overpayment. |
| Payment void | Reserve payment-void idempotency row, lock Check then Payment, require open Check and non-provider v1 payment, write correction and void fields atomically. |
| Cashier correction | Reserve correction idempotency row, lock Check and target record, validate v1 correction rules, write correction and target mutation atomically. |
| Session close | Lock TableSession and Check; recompute remaining balance in transaction; require zero balance. |
| Outbox worker claim | Use row-level claim update or `select for update skip locked`; set a bounded claim lease; each attempt writes `external_effect_attempts`. |

## Deferrable or Service-Enforced Rules

Some invariants are real but not clean simple constraints.

| Rule | Enforcement |
| --- | --- |
| Product must have at least one enabled variant to be orderable | Service transaction plus tests; optional deferred trigger later. |
| Platform role user must have `tenant_id is null` | Service validation plus integration test; optional trigger later. |
| Staff profile user tenant must match profile tenant | Composite FK if `users(tenant_id, id)` uniqueness includes nullable platform caveat; otherwise service validation and tests. |
| Staff station/hall assignment target must be enabled for active authority | Service authorization check at use time; assignments may remain for disabled objects. |
| Cashier cannot void item after payment or after disallowed preparation state | Service transaction locks Check, OrderItem, Payment summary, PreparationItem. |
| Close session requires zero balance | Service transaction computes balance under lock; database cannot express aggregate sum as simple check. |
| Audit metadata contains no secrets | Serializer/sanitizer tests; database cannot semantically inspect all secrets. |
