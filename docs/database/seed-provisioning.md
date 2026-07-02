# Seed and Provisioning Strategy

This document defines how IoTables creates required bootstrap records and one-time tenant starter data.

It is downstream of [../apps/platform/definition.md](../apps/platform/definition.md), [../modules/platform/provisioning.md](../modules/platform/provisioning.md), [../modules/platform/sector-starter-templates.md](../modules/platform/sector-starter-templates.md), [schema.md](schema.md), and [indexes-constraints.md](indexes-constraints.md).

## Core Rule

Business seed data must never run from application startup, server restart, deployment, release upgrade, or Alembic migration.

Tenant starter data is created only by the PlatformApp create-tenant flow through Provisioning, and only once per tenant/template version.

## Seed Types

| Type | Trigger | Allowed in V1 | Durable Guard |
| --- | --- | --- | --- |
| Schema/reference values | Alembic schema migration | Yes | Check constraints and code constants |
| Platform owner bootstrap | Explicit setup command/tool | Yes | Unique active Platform Owner |
| Tenant starter template | PlatformApp create tenant | Yes | `starter_template_applications` |
| Runtime demo/sample data | Startup or deployment | No | Not allowed |
| Existing-tenant product rollout | Explicit future rollout tool | Not v1 | Per-tenant rollout record |

## Not Seeded

- Orders.
- Table sessions.
- Payments.
- Preparation or delivery state.
- QR tokens.
- Customer sessions.
- Audit events except real provisioning/bootstrap events.
- Outbox messages except real external side effects such as OTP/SMS.

## Platform Owner Bootstrap

The Platform Owner is the single user of PlatformApp in v1.

Rules:

- It is created by an explicit bootstrap command/tool, not by app startup.
- The command must be idempotent and protected by the active Platform Owner uniqueness rule.
- The Platform Owner has `tenant_id = null`.
- PlatformApp access requires TOTP enrollment before normal use.
- Bootstrap must never embed a production password in migration files or committed config.
- Bootstrap writes audit event `platform_owner.created`.

If a Platform Owner already exists, the bootstrap command must fail closed or report the existing state without creating another user.

## Tenant Provisioning Overview

Tenant provisioning is initiated only by PlatformApp.

Provisioning coordinates:

- Tenant Registry;
- Identity and Access;
- Staff Access;
- Sector Starter Templates;
- Tenant Setup modules;
- Audit;
- Reliable Side Effects / OTP Messaging.

Provisioning owns orchestration and recovery state. The created records are owned by their modules after creation.

## Tenant Provisioning Phases

### Phase 1: Validate and Reserve

Run in a short transaction:

1. Validate required input: tenant name, subdomain, tenant GSM.
2. Normalize and reserve `tenants.subdomain`.
3. Insert `tenants` with `status = 'provisioning'`.
4. Insert `tenant_lifecycle_events` for provisioning start.
5. Insert `starter_template_applications` with `status = 'pending'` if a starter template is selected.
6. Insert audit event `tenant.created`.

This phase makes the provisioning attempt visible and prevents another tenant from taking the same subdomain.

If no sector starter template is selected, no starter application row is created. The tenant still needs the tenant admin user and required operational settings before activation.

### Phase 2: Apply Required Records

Run in one transaction under a tenant/provisioning lock:

1. Lock the tenant row and starter application row.
2. Recheck tenant status is `provisioning`.
3. Recheck selected starter application is not `applied`.
4. Create tenant admin user through Access.
5. Create tenant admin credential with temporary password state and first-password-change requirement.
6. If a starter template is selected, create starter staff users, credentials, profiles, roles, and assignments.
7. Create tenant operational settings.
8. If a starter template is selected, apply starter halls, tables, stations, menu categories, products, variants, and modifier records.
9. If a starter template is selected, update `starter_template_applications.status = 'applied'`.
10. Update tenant status to `active`.
11. Insert lifecycle and audit records.
12. Enqueue only provisioning-owned side effects if explicitly introduced later.

If this transaction fails, none of the starter business records should be committed.

V1 does not pre-send tenant admin or cashier OTP messages during tenant creation. OTP challenges are created when the bootstrap user starts first password setup.

When no starter template is selected, steps for starter staff and starter setup records are skipped. Tenant activation still requires tenant admin creation and tenant operational settings. The safe v1 default for `service_delivery_tracking_enabled` is `false` without a starter template; TenantApp can enable it later after halls and service staff exist.

### Phase 3: Failure Marking

If Phase 2 fails, run a separate failure transaction:

1. Lock the tenant row.
2. Set tenant status to `provisioning_failed`.
3. Store only a safe `provisioning_error` summary.
4. Set starter application status to `failed` or `recovery_needed`.
5. Insert `tenant.provisioning_failed` lifecycle/audit records.

The tenant must not become `active` until required records have committed successfully.

### Phase 4: External Side Effects

External side effects are processed after the database decision commits.

Examples:

- OTP SMS for tenant admin first password setup, triggered by first login/password setup.
- OTP SMS for cashier first password setup, triggered by first login/password setup.

Rules:

- First-login SMS failure must not rollback the committed tenant setup.
- First-login SMS failure must be visible as delivery failure/retry state.
- Provider responses must be redacted.
- DNS is manual in v1 and must not be represented as an automated side effect.

## Retry and Recovery

Provisioning retry is explicit PlatformApp recovery tooling, not automatic startup logic.

| Current State | Allowed Recovery |
| --- | --- |
| `provisioning` with pending starter application | Retry Phase 2 after locking tenant and application rows. |
| `provisioning_failed` with starter status `failed` | Retry after platform owner reviews safe error summary. |
| `provisioning_failed` with starter status `recovery_needed` | Manual recovery decision required before retry. |
| `active` with starter status `applied` | Never reapply starter data automatically. |
| Tenant sector changed after creation | Do not apply starter data. |

Retry must always check `starter_template_applications` before creating starter records.

## Starter Template Identity

The initial cafe starter uses:

| Field | Value |
| --- | --- |
| Semantic label | `cafe.v1` |
| `template_key` | `cafe_default` |
| `template_version` | `1` |
| Sector | `cafe` |

Template definitions are code/config artifacts in v1. The database stores durable application proof in `starter_template_applications`.

Template versions are immutable after release. A later `cafe.v2` must not apply automatically to existing tenants.

## Initial Cafe Starter Data

The `cafe.v1` starter creates normal tenant-owned records.

| Data Type | Created Records |
| --- | --- |
| Tenant setting | `service_delivery_tracking_enabled = true` |
| Halls | `Salon 1`, `Salon 2` |
| Tables per hall | `Masa 000`, `Masa 001`, `Masa 999` |
| Stations | `Mutfak`, `Kahve` |
| Mutfak products | `Sandviç`, `Tost`, `Kurabiye`, `Kek`, `Poğaça` with default variants/prices from `cafe.v1` |
| Kahve products | `Kapuçino`, `Americano`, `Türk Kahvesi`, `Çay`, `Latte`, `Espresso` with default variants/prices from `cafe.v1` |
| Staff users | `Kasiyer`, `Aşçı`, `Barista`, `Garson`, `Komi` |

Each starter product must have at least one default `product_variants` row. Exact starter prices are defined by the immutable `cafe.v1` template in [../modules/platform/sector-starter-templates.md](../modules/platform/sector-starter-templates.md#cafev1-template-definition). Implementation must not create an enabled/orderable product without a valid `price_minor`.

After creation, TenantApp treats these records as normal editable tenant data. They are not protected system records.

## Starter Staff Credentials and Roles

All starter staff use temporary password `admin` and must change it at first login.

| Staff User | Username | Role | Assignment | OTP |
| --- | --- | --- | --- | --- |
| Tenant Admin | tenant subdomain | `tenant_admin` | Tenant-wide admin | Required, sent to tenant GSM |
| Kasiyer | `kasiyer` | `cashier` | CashierApp | Required, sent to tenant GSM |
| Aşçı | `asci` | `station_staff` | `Mutfak` station | Not required |
| Barista | `barista` | `station_staff` | `Kahve` station | Not required |
| Garson | `garson` | `service_staff` | All starter halls | Not required |
| Komi | `komi` | `service_staff` | All starter halls | Not required |

Temporary credentials must not allow continued access after first login without password change.

## Idempotency Guards

Provisioning relies on database constraints and row locks:

| Guard | Protection |
| --- | --- |
| unique `tenant_provisioning_idempotency(actor_user_id, idempotency_key)` | Prevent duplicate Platform Owner create-tenant commands and preserve replay result. |
| unique `tenants.lower(subdomain)` | Prevent duplicate tenant domains. |
| unique active Platform Owner | Prevent multiple PlatformApp owners. |
| unique tenant username | Prevent duplicate bootstrap users. |
| unique `starter_template_applications(tenant_id, template_key, template_version)` | Prevent starter rerun. |
| unique setup names/orders inside tenant | Prevent duplicate halls, tables, stations, menu categories, and variants. |
| transaction lock on tenant/application rows | Prevent concurrent provisioning retry from double-applying records. |

The starter application row is the durable proof. Existence of some starter records is not enough proof because TenantApp may edit or delete those records after creation.

## Failure Scenarios

| Failure | Required Outcome |
| --- | --- |
| Duplicate subdomain | Reject before creating tenant records. |
| Validation fails | Reject before creating tenant records. |
| Starter template missing | Tenant remains or becomes `provisioning_failed`; no active tenant. |
| Staff user creation fails | Starter transaction rolls back; tenant marked failed. |
| Menu/table/station creation fails | Starter transaction rolls back; tenant marked failed. |
| Commit succeeds but first-login SMS later fails | Tenant remains active; SMS delivery retries or shows failure in the OTP/password setup flow. |
| Worker crashes after enqueue | Outbox retry resumes. |
| Retry called after success | Return existing applied state; do not create records. |

## Recovery Safety

Recovery tools must show:

- tenant identity;
- tenant status;
- starter application status;
- safe failure summary;
- whether any required setup records are missing;
- whether SMS/OTP side effects are pending or failed;
- audit trail for provisioning attempts.

Recovery tools must not:

- silently reapply `cafe.v1`;
- mutate tenant runtime records;
- hide previous failure history;
- change immutable tenant name or subdomain;
- pretend DNS was automated.

## Relationship to Alembic Migrations

Alembic migrations may create tables, constraints, and reference-compatible value checks.

Alembic migrations must not:

- create tenant starter halls/tables/stations/menu/staff;
- reapply starter templates to existing tenants;
- create runtime demo orders/payments;
- retry failed OTP/SMS;
- fix provisioning failures by inserting business records without recovery tooling.

If a future release needs to apply new business records to existing tenants, that is a product rollout or recovery workflow, not a schema migration.

## Verification Requirements

Provisioning implementation must have tests for:

- successful `cafe.v1` tenant creation;
- duplicate subdomain rejection;
- duplicate provisioning request/retry safety;
- starter application applied exactly once;
- tenant remains inactive on starter failure;
- successful DB commit with later first-login SMS failure;
- retry after failed provisioning;
- no starter rerun after tenant sector change;
- starter products cannot be orderable without valid variants/prices;
- correct station and hall staff assignments.

## Open Questions

None currently.
