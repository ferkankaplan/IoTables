# PostgreSQL Schema

This document defines the v1 physical PostgreSQL schema for IoTables.

It is derived from [../data-model.md](../data-model.md) and the owning module documents. It does not replace them. App documents define behavior; module documents define ownership and invariants; this document defines how those decisions are stored.

## Scope

- Database: PostgreSQL 18.4 target, as recorded in [../stack.md](../stack.md).
- Application shape: modular monolith.
- PostgreSQL schema namespace: `public` in v1.
- Tenant model: shared tables with `tenant_id` on every tenant-owned record.
- Physical multi-tenant isolation: row-level ownership through `tenant_id`, enforced by foreign keys, service guards, and tests.
- Separate PostgreSQL schemas per module are out of v1. Module boundaries are enforced by code ownership, migrations, and documented table ownership.

## Type Conventions

| Concept | PostgreSQL Type | Rule |
| --- | --- | --- |
| Primary IDs | `uuid` | Application-generated UUIDs are preferred so tests and domain services do not depend on database-side UUID generation. |
| Timestamps | `timestamptz` | Store all times as timezone-aware UTC values. |
| Money | `bigint` minor units | Store TRY kurus or other ISO currency minor units. Do not store money as floating point. |
| Currency | `char(3)` | ISO 4217 code, `TRY` default in v1. |
| Status/enums | `text` with named `CHECK` constraints | Easier Alembic evolution than PostgreSQL enum types while preserving database enforcement. |
| Secrets/tokens | `text` hash or encrypted `bytea` | Raw password, OTP, session, QR token, and display credential values are never stored. |
| Flexible snapshots | `jsonb` | Only for immutable order snapshots, modifier selections, audit metadata, and redacted side-effect payload refs. |
| Human text | `text` | Validate length at API/domain layer unless a hard database bound is useful. |

## Shared Columns

Unless explicitly stated otherwise:

- `id uuid primary key` exists on independently addressed records.
- `tenant_id uuid not null references tenants(id)` exists on tenant-owned records.
- `created_at timestamptz not null` exists on records that are created by user/system activity.
- `updated_at timestamptz` exists only on mutable records where the latest state is edited in place.
- Historical records use append-only rows instead of `updated_at` when mutation would hide history.

## Domain Value Sets

These are stored as `text` columns with named `CHECK` constraints.

| Value Set | Values |
| --- | --- |
| `tenant_sector` | `cafe` in v1 |
| `tenant_status` | `provisioning`, `active`, `suspended`, `provisioning_failed` |
| `starter_application_status` | `pending`, `applied`, `failed`, `recovery_needed` |
| `tenant_provisioning_idempotency_status` | `processing`, `completed`, `failed` |
| `user_status` | `active`, `disabled` |
| `app_scope` | `platform`, `tenant`, `cashier`, `station`, `service` |
| `platform_role` | `platform_owner` |
| `staff_role` | `tenant_admin`, `cashier`, `station_staff`, `service_staff` |
| `assignment_status` | `active`, `revoked` |
| `display_credential_status` | `active`, `revoked` |
| `availability_state` | `available`, `unavailable` |
| `cart_status` | `active`, `submitted`, `abandoned` |
| `idempotency_status` | `processing`, `completed`, `failed` |
| `table_session_status` | `open`, `closed` |
| `check_status` | `open`, `closed` |
| `order_status` | `submitted` in v1 |
| `order_channel` | `dine_in_qr` in v1 |
| `preparation_status` | `pending`, `preparing`, `ready`, `cannot_prepare` |
| `delivery_status` | `picked_up`, `delivered` |
| `payment_method` | `cash`, `card`, `transfer` |
| `payment_status` | `recorded`, `voided` |
| `price_adjustment_type` | `tax`, `discount`, `service_charge`, `campaign`, `correction` |
| `cashier_correction_type` | `note`, `item_void`, `payment_void` |
| `otp_purpose` | `tenant_admin_first_password`, `cashier_first_password` |
| `otp_attempt_result` | `success`, `failed`, `locked`, `expired` |
| `message_delivery_status` | `queued`, `sent`, `failed` |
| `outbox_effect_type` | `sms`, `printer`, `fiscal`, `payment_provider`, `dns`, `notification`, `device` |
| `outbox_status` | `pending`, `claimed`, `completed`, `failed` |
| `external_effect_result` | `success`, `retryable_failure`, `permanent_failure`, `timeout` |

## Platform

### `tenants`

Owned by: Platform / Tenant Registry

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `name` | `text` | Required, immutable |
| `subdomain` | `text` | Required, immutable, lowercase unique |
| `gsm_number` | `text` | Required, editable, audited |
| `sector` | `text` | Nullable; `tenant_sector` check when present |
| `capacity` | `integer` | Optional, informational in v1 |
| `address` | `text` | Optional |
| `status` | `text` | `tenant_status` check |
| `dns_ready` | `boolean` | Manual DNS checklist flag |
| `provisioning_error` | `text` | Safe error summary only |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last profile/status update |

### `tenant_operational_settings`

Owned by: Tenant Setup

| Column | Type | Notes |
| --- | --- | --- |
| `tenant_id` | `uuid` | Primary key, FK to `tenants.id` |
| `public_display_name` | `text` | Optional customer-visible name |
| `service_delivery_tracking_enabled` | `boolean` | Controls ServiceStaffApp runtime authority |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `tenant_health`

Owned by: Platform / Tenant Registry

Rebuildable platform read model. It must not contain tenant runtime detail.

| Column | Type | Notes |
| --- | --- | --- |
| `tenant_id` | `uuid` | Primary key, FK to `tenants.id` |
| `lifecycle_state` | `text` | Tenant status summary |
| `setup_state` | `text` | Setup readiness summary |
| `starter_template_state` | `text` | Starter application summary |
| `tenant_admin_bootstrap_state` | `text` | First admin readiness summary |
| `dns_ready` | `boolean` | Copied high-level readiness flag |
| `runtime_error_summary` | `text` | Safe platform-visible summary |
| `updated_at` | `timestamptz` | Last recalculation |

### `tenant_lifecycle_events`

Owned by: Platform / Tenant Registry

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `previous_status` | `text` | Nullable for creation |
| `next_status` | `text` | Required |
| `actor_user_id` | `uuid` | Nullable FK to `users.id` |
| `reason` | `text` | Required for suspend/reactivate/failure recovery |
| `created_at` | `timestamptz` | Append-only event time |

### `starter_template_applications`

Owned by: Platform / Sector Starter Templates

Starter template definitions are code/config artifacts in v1. This table is the durable proof that a template was applied to a tenant.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `sector` | `text` | Sector used at creation |
| `template_key` | `text` | Example: `cafe_default` |
| `template_version` | `integer` | Immutable template version |
| `status` | `text` | `starter_application_status` check |
| `failure_summary` | `text` | Redacted failure detail |
| `applied_at` | `timestamptz` | Successful completion time |
| `created_at` | `timestamptz` | Start time |
| `updated_at` | `timestamptz` | Latest status update |

### `tenant_provisioning_idempotency`

Owned by: Platform / Provisioning

Stores HTTP idempotency reservations and completed replay payloads for `POST /api/v1/platform/tenants`.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `actor_user_id` | `uuid` | Platform owner FK to `users.id` |
| `idempotency_key` | `text` | Client request key |
| `request_hash` | `text` | Server-computed normalized tenant creation fingerprint |
| `tenant_id` | `uuid` | Nullable FK to completed tenant |
| `response_payload` | `jsonb` | Completed `ProvisioningResult` replay payload |
| `status` | `text` | `tenant_provisioning_idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

## Access

### `users`

Owned by: Identity and Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | Nullable only for platform owner |
| `username` | `text` | Unique in tenant/platform scope |
| `status` | `text` | `user_status` check |
| `first_password_change_required` | `boolean` | Bootstrap safety flag |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last status/update time |

### `credentials`

Owned by: Identity and Access

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | `uuid` | Primary key, FK to `users.id` |
| `password_hash` | `text` | Argon2/bcrypt-style encoded hash, never plaintext |
| `bootstrap_credential` | `boolean` | True until first password setup |
| `changed_at` | `timestamptz` | Last password change |

### `login_sessions`

Owned by: Identity and Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | Nullable only for platform session |
| `user_id` | `uuid` | FK to `users.id` |
| `app_scope` | `text` | `app_scope` check |
| `session_token_hash` | `text` | Unique opaque session token hash |
| `issued_at` | `timestamptz` | Creation time |
| `expires_at` | `timestamptz` | Hard expiry |
| `revoked_at` | `timestamptz` | Nullable explicit revoke time |

### `platform_role_assignments`

Owned by: Identity and Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `user_id` | `uuid` | FK to `users.id` |
| `role` | `text` | `platform_role` check |
| `status` | `text` | `user_status` check |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last status update |

### `totp_factors`

Owned by: Identity and Access

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | `uuid` | Primary key, FK to `users.id` |
| `secret_ciphertext` | `bytea` | Encrypted TOTP secret |
| `enrolled_at` | `timestamptz` | Enrollment time |
| `enabled` | `boolean` | Required for PlatformApp access |

### `staff_profiles`

Owned by: Staff Access

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | `uuid` | Primary key, FK to `users.id` |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `display_name` | `text` | Staff label |
| `status` | `text` | `user_status` check |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last status/update time |

### `staff_role_assignments`

Owned by: Staff Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `user_id` | `uuid` | FK to `users.id` |
| `role` | `text` | `staff_role` check |
| `status` | `text` | `assignment_status` check |
| `created_at` | `timestamptz` | Assignment time |
| `revoked_at` | `timestamptz` | Nullable revoke time |

### `staff_station_assignments`

Owned by: Staff Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `user_id` | `uuid` | FK to `users.id` |
| `station_id` | `uuid` | FK to `stations.id` |
| `status` | `text` | `assignment_status` check |
| `created_at` | `timestamptz` | Assignment time |
| `revoked_at` | `timestamptz` | Nullable revoke time |

### `staff_hall_assignments`

Owned by: Staff Access

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `user_id` | `uuid` | FK to `users.id` |
| `hall_id` | `uuid` | FK to `halls.id` |
| `status` | `text` | `assignment_status` check |
| `created_at` | `timestamptz` | Assignment time |
| `revoked_at` | `timestamptz` | Nullable revoke time |

## Tenant Setup

### `halls`

Owned by: Venue Layout

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `name` | `text` | Hall name |
| `display_order` | `integer` | Ordered hall list |
| `enabled` | `boolean` | Disabled halls cannot be active use targets |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `venue_tables`

Owned by: Venue Layout

`venue_tables` is used instead of `tables` to avoid confusing the domain table with database tables.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `hall_id` | `uuid` | FK to `halls.id` |
| `name` | `text` | Table label |
| `display_order` | `integer` | Ordered position inside hall |
| `enabled` | `boolean` | Disabled tables cannot accept new orders |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `stations`

Owned by: Station Setup

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `name` | `text` | Station name |
| `display_order` | `integer` | Tenant/staff UI order |
| `enabled` | `boolean` | Disabled stations cannot receive new items |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `menu_categories`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `name` | `text` | Customer-visible name |
| `display_order` | `integer` | Menu order |
| `enabled` | `boolean` | Visibility/orderability flag |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `product_services`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `category_id` | `uuid` | FK to `menu_categories.id` |
| `station_id` | `uuid` | FK to `stations.id` |
| `name` | `text` | Customer-visible product/service name |
| `description` | `text` | Optional |
| `image_ref` | `text` | Optional asset reference |
| `enabled` | `boolean` | Disabled products cannot be ordered |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `product_variants`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `product_service_id` | `uuid` | FK to `product_services.id` |
| `name` | `text` | Variant label |
| `price_minor` | `bigint` | Current price in minor currency unit |
| `currency_code` | `char(3)` | `TRY` default in v1 |
| `display_order` | `integer` | Variant order |
| `is_default` | `boolean` | At most one default per product |
| `enabled` | `boolean` | Disabled variants cannot be ordered |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `availability_overrides`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `product_service_id` | `uuid` | FK to `product_services.id` |
| `product_variant_id` | `uuid` | Nullable FK to `product_variants.id` |
| `state` | `text` | `availability_state` check |
| `reason` | `text` | Optional staff-visible reason |
| `starts_at` | `timestamptz` | Nullable start |
| `expires_at` | `timestamptz` | Nullable expiry |
| `created_by_user_id` | `uuid` | FK to `users.id` |
| `created_at` | `timestamptz` | Creation time |

### `modifier_groups`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `product_service_id` | `uuid` | FK to `product_services.id` |
| `name` | `text` | Group label |
| `required` | `boolean` | Whether customer must select |
| `min_selections` | `integer` | Minimum selected options |
| `max_selections` | `integer` | Maximum selected options |
| `display_order` | `integer` | UI order |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

### `modifier_options`

Owned by: Menu Catalog

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `modifier_group_id` | `uuid` | FK to `modifier_groups.id` |
| `name` | `text` | Option label |
| `price_delta_minor` | `bigint` | Signed price delta |
| `currency_code` | `char(3)` | `TRY` default in v1 |
| `available` | `boolean` | Orderability |
| `display_order` | `integer` | UI order |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last update |

## Table Display and Presence

### `table_display_claims`

Owned by: Table Display Provisioning

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `claim_hash` | `text` | Unique one-time claim hash |
| `created_by_user_id` | `uuid` | Tenant admin actor |
| `expires_at` | `timestamptz` | Short claim lifetime |
| `consumed_at` | `timestamptz` | Atomic consumption time |
| `created_at` | `timestamptz` | Creation time |

### `table_display_credentials`

Owned by: Table Display Provisioning

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `credential_hash` | `text` | Unique display credential hash |
| `status` | `text` | `display_credential_status` check |
| `provisioned_at` | `timestamptz` | Activation time |
| `revoked_at` | `timestamptz` | Nullable revoke time |
| `last_seen_at` | `timestamptz` | Last successful QR fetch |

### `table_access_tokens`

Owned by: Ordering / Table Presence

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `token_hash` | `text` | Unique one-time QR token hash |
| `expires_at` | `timestamptz` | 60 seconds in v1 |
| `consumed_at` | `timestamptz` | Atomic consumption time |
| `created_at` | `timestamptz` | Issued time |

## Customer Ordering

### `customer_ordering_sessions`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `table_session_id` | `uuid` | Nullable FK to `table_sessions.id` |
| `cookie_token_hash` | `text` | Unique browser session token hash |
| `presence_valid_until` | `timestamptz` | Fresh QR presence window |
| `expires_at` | `timestamptz` | 30 minutes in v1 |
| `last_seen_at` | `timestamptz` | Last activity |
| `created_at` | `timestamptz` | Session creation |
| `updated_at` | `timestamptz` | Presence/session update |

### `customer_carts`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `customer_ordering_session_id` | `uuid` | FK to `customer_ordering_sessions.id` |
| `status` | `text` | `cart_status` check |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last cart mutation |

### `customer_cart_items`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `cart_id` | `uuid` | FK to `customer_carts.id` |
| `client_cart_item_id` | `text` | Browser-generated stable item key |
| `product_service_id` | `uuid` | FK to `product_services.id` |
| `product_variant_id` | `uuid` | FK to `product_variants.id` |
| `quantity` | `integer` | Positive |
| `selected_modifiers` | `jsonb` | Selected modifier option IDs and counts |
| `note` | `text` | Optional customer note |
| `estimated_price_minor` | `bigint` | Display only, never authoritative |
| `created_at` | `timestamptz` | Creation time |
| `updated_at` | `timestamptz` | Last item mutation |

### `order_submit_idempotency`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `customer_ordering_session_id` | `uuid` | FK to `customer_ordering_sessions.id` |
| `idempotency_key` | `text` | Client request key |
| `request_hash` | `text` | Normalized request fingerprint |
| `order_id` | `uuid` | Nullable FK to `orders.id` until completed |
| `status` | `text` | `idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

### `orders`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `customer_ordering_session_id` | `uuid` | FK to `customer_ordering_sessions.id` |
| `table_session_id` | `uuid` | FK to `table_sessions.id` |
| `status` | `text` | `order_status` check |
| `order_channel` | `text` | `order_channel` check |
| `submitted_at` | `timestamptz` | Customer-visible order time |
| `created_at` | `timestamptz` | Storage time |

### `order_items`

Owned by: Customer Ordering

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `order_id` | `uuid` | FK to `orders.id` |
| `product_service_id` | `uuid` | FK to `product_services.id` |
| `product_variant_id` | `uuid` | FK to `product_variants.id` |
| `station_id` | `uuid` | FK to `stations.id`, routing snapshot |
| `name_snapshot` | `text` | Product name at submit time |
| `variant_name_snapshot` | `text` | Variant name at submit time |
| `unit_price_minor` | `bigint` | Server-calculated snapshot |
| `currency_code` | `char(3)` | Snapshot currency |
| `modifier_snapshot` | `jsonb` | Selected modifiers and price deltas |
| `quantity` | `integer` | Positive |
| `note` | `text` | Customer note |
| `voided_at` | `timestamptz` | Nullable correction time |
| `voided_by_user_id` | `uuid` | Nullable FK to `users.id` |
| `void_reason` | `text` | Required when voided |
| `created_at` | `timestamptz` | Creation time |

## Table Session and Settlement

### `table_sessions`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `status` | `text` | `table_session_status` check |
| `opened_at` | `timestamptz` | First order time |
| `closed_at` | `timestamptz` | Nullable closure time |
| `created_at` | `timestamptz` | Storage time |
| `updated_at` | `timestamptz` | Last status update |

### `checks`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_session_id` | `uuid` | FK to `table_sessions.id` |
| `status` | `text` | `check_status` check |
| `opened_at` | `timestamptz` | Creation/open time |
| `closed_at` | `timestamptz` | Nullable closure time |

### `price_adjustments`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `order_item_id` | `uuid` | Nullable FK to `order_items.id` |
| `type` | `text` | `price_adjustment_type` check |
| `amount_minor` | `bigint` | Signed amount |
| `currency_code` | `char(3)` | `TRY` default in v1 |
| `reason` | `text` | Required for correction |
| `created_by_user_id` | `uuid` | FK to `users.id` |
| `created_at` | `timestamptz` | Append-only time |

### `session_closures`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `table_session_id` | `uuid` | Unique FK to `table_sessions.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `cashier_user_id` | `uuid` | FK to `users.id` |
| `reason` | `text` | Nullable unless recovery requires it |
| `closed_at` | `timestamptz` | Closure time |

### `payments`

Owned by: Payments

V1 represents `PaymentVoid` as immutable void fields on this table plus a required `cashier_corrections` row. No separate `payment_voids` table is created in v1.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `amount_minor` | `bigint` | Positive payment amount |
| `currency_code` | `char(3)` | `TRY` default in v1 |
| `method` | `text` | `payment_method` check |
| `status` | `text` | `payment_status` check |
| `cashier_user_id` | `uuid` | FK to `users.id` |
| `received_at` | `timestamptz` | Payment time |
| `voided_at` | `timestamptz` | Nullable void time |
| `voided_by_user_id` | `uuid` | Nullable FK to `users.id` |
| `void_reason` | `text` | Required when voided |
| `created_at` | `timestamptz` | Storage time |
| `updated_at` | `timestamptz` | Status update time |

### `payment_idempotency`

Owned by: Payments

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `idempotency_key` | `text` | Cashier request key |
| `request_hash` | `text` | Normalized request fingerprint |
| `payment_id` | `uuid` | Nullable FK to `payments.id` until completed |
| `status` | `text` | `idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

### `payment_void_idempotency`

Owned by: Payments

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `payment_id` | `uuid` | FK to `payments.id` |
| `idempotency_key` | `text` | Cashier request key |
| `request_hash` | `text` | Normalized payment/actor/reason fingerprint |
| `status` | `text` | `idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

### `cashier_corrections`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `type` | `text` | `cashier_correction_type` check |
| `target_type` | `text` | Target model label |
| `target_id` | `uuid` | Target record ID |
| `reason` | `text` | Required |
| `created_by_user_id` | `uuid` | Cashier actor FK to `users.id` |
| `created_at` | `timestamptz` | Append-only time |

### `cashier_correction_idempotency`

Owned by: Table Session and Billing

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `check_id` | `uuid` | FK to `checks.id` |
| `idempotency_key` | `text` | Cashier request key |
| `request_hash` | `text` | Normalized correction fingerprint |
| `cashier_correction_id` | `uuid` | Nullable FK to `cashier_corrections.id` until completed |
| `status` | `text` | `idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

## Fulfillment

### `preparation_items`

Owned by: Preparation

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `order_item_id` | `uuid` | Unique FK to `order_items.id` |
| `station_id` | `uuid` | FK to `stations.id` |
| `status` | `text` | `preparation_status` check |
| `cannot_prepare_reason` | `text` | Required when status is `cannot_prepare` |
| `updated_by_user_id` | `uuid` | Nullable FK to `users.id` |
| `updated_at` | `timestamptz` | Last transition time |
| `created_at` | `timestamptz` | Queue creation time |

### `preparation_transitions`

Owned by: Preparation

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `preparation_item_id` | `uuid` | FK to `preparation_items.id` |
| `actor_user_id` | `uuid` | FK to `users.id` |
| `from_status` | `text` | Nullable only for initial row if used |
| `to_status` | `text` | Required |
| `reason` | `text` | Required for `cannot_prepare` |
| `created_at` | `timestamptz` | Append-only transition time |

### `delivery_states`

Owned by: Service Delivery

Created on first pickup or direct delivery when service delivery tracking is enabled.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `order_item_id` | `uuid` | Unique FK to `order_items.id` |
| `status` | `text` | `delivery_status` check |
| `updated_by_user_id` | `uuid` | FK to `users.id` |
| `updated_at` | `timestamptz` | Last transition time |
| `created_at` | `timestamptz` | First pickup or direct delivery time |

### `delivery_transitions`

Owned by: Service Delivery

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `delivery_state_id` | `uuid` | FK to `delivery_states.id` |
| `order_item_id` | `uuid` | FK to `order_items.id`, denormalized for audit/query |
| `actor_user_id` | `uuid` | FK to `users.id` |
| `from_status` | `text` | Nullable for first pickup |
| `to_status` | `text` | Required |
| `created_at` | `timestamptz` | Append-only transition time |

### `delivery_bulk_idempotency`

Owned by: Service Delivery

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `actor_user_id` | `uuid` | FK to `users.id` |
| `table_id` | `uuid` | FK to `venue_tables.id` |
| `idempotency_key` | `text` | Service staff request key |
| `request_hash` | `text` | Normalized actor/table/item fingerprint |
| `delivered_order_item_ids` | `jsonb` | Stable replay result for completed command |
| `status` | `text` | `idempotency_status` check |
| `created_at` | `timestamptz` | Reservation time |
| `completed_at` | `timestamptz` | Nullable completion time |

## OTP and Messaging

### `otp_challenges`

Owned by: OTP / Messaging

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `user_id` | `uuid` | FK to `users.id` |
| `purpose` | `text` | `otp_purpose` check |
| `target_gsm` | `text` | Snapshot at challenge creation |
| `code_hash` | `text` | Non-recoverable OTP hash |
| `expires_at` | `timestamptz` | 5 minutes in v1 |
| `verified_at` | `timestamptz` | Nullable success time |
| `created_at` | `timestamptz` | Challenge creation |

### `otp_attempts`

Owned by: OTP / Messaging

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `otp_challenge_id` | `uuid` | FK to `otp_challenges.id` |
| `attempt_no` | `integer` | Monotonic per challenge; v1 range 1-5 |
| `result` | `text` | `otp_attempt_result` check |
| `created_at` | `timestamptz` | Attempt time |

### `message_deliveries`

Owned by: OTP / Messaging

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | FK to `tenants.id` |
| `otp_challenge_id` | `uuid` | FK to `otp_challenges.id` |
| `delivery_no` | `integer` | Monotonic per challenge; v1 range 1-3 |
| `provider` | `text` | SMS adapter name |
| `provider_message_ref` | `text` | Nullable provider reference |
| `status` | `text` | `message_delivery_status` check; queued/sent/failed lifecycle guarded |
| `error_summary` | `text` | Redacted error required for failed delivery |
| `created_at` | `timestamptz` | Attempt start |
| `completed_at` | `timestamptz` | Nullable completion |

## Governance

### `audit_events`

Owned by: Audit

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | Nullable for platform-global actions |
| `actor_user_id` | `uuid` | Nullable system actor FK to `users.id` |
| `action` | `text` | Structured action name |
| `target_type` | `text` | Target model label |
| `target_id` | `text` | Text to support UUID or natural platform identifiers |
| `reason` | `text` | Required for sensitive actions |
| `metadata` | `jsonb` | Safe JSON object metadata, no secrets |
| `created_at` | `timestamptz` | Append-only event time |

Allowed v1 action names are owned by Governance. The current database catalog includes `platform_owner.created`, `platform_owner.totp_enrolled`, `tenant.created`, `tenant.provisioning_failed`, `tenant.activated`, `tenant.suspended`, `tenant.gsm_changed`, `tenant.profile_updated`, `tenant.dns_ready_changed`, `starter_template.applied`, `user.created`, `user.disabled`, `password.changed`, `otp.verified`, `table_display.provisioned`, `table_display.revoked`, `order.submitted`, `preparation.status_changed`, `delivery.status_changed`, `payment.recorded`, `payment.voided`, `session.closed`, and `cashier.correction_applied`.

### `outbox_messages`

Owned by: Reliable Side Effects

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `tenant_id` | `uuid` | Nullable for platform-global effects |
| `effect_type` | `text` | `outbox_effect_type` check |
| `aggregate_type` | `text` | Source aggregate label |
| `aggregate_id` | `text` | Source aggregate ID |
| `payload_ref` | `jsonb` | Redacted JSON object payload reference |
| `idempotency_ref` | `text` | Stable duplicate-protection reference |
| `status` | `text` | `outbox_status` check with claim/completion lifecycle guards |
| `next_attempt_at` | `timestamptz` | Worker scheduling |
| `claimed_by` | `text` | Nullable worker identity |
| `claimed_at` | `timestamptz` | Nullable claim time |
| `claim_expires_at` | `timestamptz` | Nullable worker lease expiry |
| `created_at` | `timestamptz` | Enqueue time |
| `completed_at` | `timestamptz` | Required only for completed messages |

### `external_effect_attempts`

Owned by: Reliable Side Effects

| Column | Type | Notes |
| --- | --- | --- |
| `id` | `uuid` | Primary key |
| `outbox_message_id` | `uuid` | FK to `outbox_messages.id` |
| `attempt_no` | `integer` | Monotonic per outbox message |
| `started_at` | `timestamptz` | Attempt start |
| `completed_at` | `timestamptz` | Nullable completion |
| `result` | `text` | `external_effect_result` check with completion lifecycle guard |
| `result_summary` | `text` | Redacted provider response summary required for non-success results |

## Not Persisted as Tables in V1

| Concept | V1 Storage Decision |
| --- | --- |
| `Sector` | Stored as checked `tenants.sector`; sector metadata can live in code/config for v1. |
| `StarterTemplate` | Stored as versioned code/config; durable application proof is `starter_template_applications`. |
| `TableState` | Query/read model derived from table/session/order/fulfillment/payment tables. |
| `BillSummary` | Calculated from Check, OrderItem snapshots, corrections, adjustments, and payments. |
| `StationWorkload` | Derived from `preparation_items` and `preparation_transitions`. |
| `ServiceQueue` | Derived from ready `preparation_items` and `delivery_states`. |
| `ServiceWorkload` | Derived from `preparation_items` and `delivery_transitions`. |
| `PaymentVoid` | Represented by immutable void fields on `payments` plus `cashier_corrections`. |
| `AuditMetadata` | Embedded in `audit_events.metadata`. |
| `AuditReason` | Stored in the owning record's `reason` column. |
