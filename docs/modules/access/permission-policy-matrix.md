# Permission Policy Matrix

This document is the current release authorization source for module command/query contracts.

It answers two questions:

1. Which actor may call each module contract?
2. Which server-side scope checks are required?

It is downstream of app definitions, app visibility documents, and module contracts. API endpoint contracts must wrap these rules without weakening them.

## Authorization Layers

Every protected operation is checked in layers.

| Layer | Owning Module | Rule |
| --- | --- | --- |
| Tenant availability | Platform / Tenant Registry | Tenant must be resolvable and active unless the operation is platform/recovery-only. |
| Human identity and app scope | Identity and Access | Authenticated staff/admin sessions must match tenant and app scope. |
| Staff role and operational scope | Staff Access | Staff roles and station/hall scopes are checked server-side. |
| Anonymous customer presence | Ordering / Table Presence | CustomerApp protected actions require a CustomerOrderingSession and sometimes fresh QR presence. |
| Display authentication | Tenant Setup / Table Display Provisioning | ESP32 display requests use display credentials, not human login. |
| Domain state | Owning domain module | Current state must allow the command: open Check, active table, ready item, etc. |
| Evidence/safety | Governance and database | Audit, idempotency, constraints, row locks, and outbox rules are mandatory where specified. |

Frontend visibility is never authorization proof.

## Actor Types

| Actor | Identity Source | Scope |
| --- | --- | --- |
| Platform Owner | Identity user with platform role and `tenant_id = null` | Global platform scope in the current release |
| Tenant Admin | Tenant user with `tenant_admin` role | Own tenant |
| Cashier | Tenant user with `cashier` role | Own tenant |
| Station Staff | Tenant user with `station_staff` role | Own tenant plus assigned stations |
| Service Staff | Tenant user with `service_staff` role | Own tenant plus assigned halls |
| Anonymous Customer | CustomerOrderingSession cookie plus fresh table presence where required | One tenant/table/browser session |
| ESP32 Table Display | TableDisplayCredential | One tenant/table display |
| Provisioning | Internal system workflow started by Platform Owner | Tenant creation/recovery workflow |
| Worker | Internal background worker | Claimed side-effect/outbox work only |
| Bootstrap Tool | Explicit setup command/tool | Initial Platform Owner creation only |

## App Entry Matrix

| App / Surface | Allowed Actor | Required Guards |
| --- | --- | --- |
| PlatformApp | Platform Owner | Platform session and active platform owner |
| TenantApp | Tenant Admin | Tenant active, tenant session, `tenant_admin` role, own tenant |
| CustomerApp | Anonymous Customer | Tenant active; public menu browsing allowed; order/table/balance protected by CustomerOrderingSession and fresh presence where required |
| StationStaffApp | Station Staff | Tenant active, station app scope, `station_staff` role, assigned station for queue mutations |
| ServiceStaffApp | Service Staff | Tenant active, service app scope, `service_staff` role, service tracking enabled, assigned hall for queue mutations |
| CashierApp | Cashier | Tenant active, cashier app scope, `cashier` role |
| ESP32 QR fetch | ESP32 Table Display | Active table display credential, table enabled, tenant active |
| Background worker | Worker | Internal worker identity/config; may only claim side-effect work |

## Platform Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `tenant_registry.register_identity` | Provisioning | Provisioning was started by Platform Owner and tenant-creation OTP was verified | Name/subdomain/GSM required; subdomain unique; GSM unique |
| `tenant_registry.update_profile` | PlatformApp | Platform Owner global | TenantApp cannot change name, subdomain, GSM, lifecycle, or platform-only health |
| `tenant_registry.change_status` | PlatformApp | Platform Owner | Valid lifecycle transition; reason required for suspend/reactivate/recovery |
| `tenant_registry.mark_provisioning_failed` | Provisioning | Internal provisioning workflow | Tenant not active; redacted failure summary |
| `tenant_registry.activate_tenant` | Provisioning | Internal provisioning workflow | Required setup records committed |
| `provisioning.start_tenant` | PlatformApp | Platform Owner | Required tenant fields; tenant-creation OTP proof; supported sector; starter idempotency |
| `provisioning.retry_failed` | PlatformApp | Platform Owner | Tenant failed/incomplete; completed starter data must not rerun |
| `provisioning.mark_recovery_needed` | Platform recovery tooling | Platform Owner/recovery authority | Preserve failure history |
| `sector_starter_templates.apply_template` | Provisioning | Internal provisioning lock | Template active; application not already applied |
| `sector_starter_templates.mark_failed` | Provisioning | Internal provisioning/recovery | Safe failure summary only |

## Platform Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `tenant_registry.resolve_by_subdomain` | TenantApp, CustomerApp, CashierApp, StationStaffApp, ServiceStaffApp | Tenant app route context | Tenant routing and availability only |
| `tenant_registry.get_profile` | PlatformApp, TenantApp | Platform Owner or Tenant Admin own tenant | Tenant identity/profile without runtime records |
| `tenant_registry.get_health` | PlatformApp | Platform Owner | High-level health; no tenant runtime detail |
| `tenant_registry.get_lifecycle_events` | PlatformApp | Platform Owner | Tenant lifecycle timeline |
| `provisioning.get_state` | PlatformApp | Platform Owner | Provisioning state and safe failure summary |
| `provisioning.get_recovery_summary` | PlatformApp | Platform Owner | Recovery summary without runtime mutation |
| `sector_starter_templates.list_sectors` | PlatformApp | Platform Owner | Supported sector options |
| `sector_starter_templates.get_template` | PlatformApp, Provisioning | Platform Owner or internal provisioning | Immutable template definition |
| `sector_starter_templates.get_application_state` | PlatformApp, TenantApp, Provisioning | Platform Owner, Tenant Admin own tenant, or internal provisioning | Starter application status only |

## Access Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `identity_access.create_platform_owner` | Bootstrap Tool | Explicit setup command; no existing active Platform Owner | No automatic startup seed |
| `identity_access.create_bootstrap_user` | Provisioning, TenantApp | Provisioning or Tenant Admin own tenant | Username unique in tenant/platform scope |
| `identity_access.authenticate` | PlatformApp, TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | App scope must match target app and tenant | Disabled users fail; first-login users forced to setup |
| `identity_access.begin_first_password_setup` | TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | Setup token/user must match app/tenant | No first-password OTP in the current release |
| `identity_access.complete_first_password_setup` | TenantApp, CashierApp, StationStaffApp, ServiceStaffApp | Setup token/user must match app/tenant | Password policy only; no first-password OTP in the current release |
| `identity_access.change_password` | Authenticated user | Own active user session | Current password valid |
| `identity_access.enroll_totp` | PlatformApp | Platform Owner | Reserved for future PlatformApp hardening; not required by current release login |
| `identity_access.logout_or_revoke_session` | Authenticated user, TenantApp admin recovery, Platform recovery | Own session, Tenant Admin own tenant, or Platform recovery | Revoked/expired sessions fail closed |
| `identity_access.disable_user` | TenantApp, Platform recovery | Tenant Admin own tenant or Platform recovery | Cannot silently disable only active Platform Owner |
| `staff_access.upsert_staff_profile` | Provisioning, TenantApp | Provisioning or Tenant Admin own tenant | User belongs to tenant |
| `staff_access.assign_role` | Provisioning, TenantApp | Provisioning or Tenant Admin own tenant | Role supported; user belongs to tenant |
| `staff_access.revoke_role` | TenantApp | Tenant Admin own tenant | Cannot revoke own last tenant admin role without recovery rule |
| `staff_access.assign_station` | Provisioning, TenantApp | Provisioning or Tenant Admin own tenant | Station belongs to tenant; user has or is receiving station role |
| `staff_access.revoke_station` | TenantApp | Tenant Admin own tenant | Active assignment exists |
| `staff_access.assign_hall` | Provisioning, TenantApp | Provisioning or Tenant Admin own tenant | Hall belongs to tenant; user has or is receiving service role |
| `staff_access.revoke_hall` | TenantApp | Tenant Admin own tenant | Active assignment exists |
| `otp_messaging.create_challenge` | PlatformApp, Identity and Access | Tenant creation or password reset flow owns challenge | Purpose supported; target GSM snapshotted |
| `otp_messaging.send_otp` | PlatformApp, Identity and Access, Worker | Tenant creation/password reset flow owns challenge or worker claim | Challenge active; send limit respected |
| `otp_messaging.verify_otp` | PlatformApp, Identity and Access | Tenant creation/password reset flow owns challenge | Challenge active; attempt limit respected |
| `otp_messaging.expire_or_lock_challenge` | OTP Messaging | Internal policy | Challenge terminal state rules |

## Access Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `identity_access.get_login_requirements` | Login surfaces | Safe login response only | Do not leak hidden user/tenant existence |
| `identity_access.validate_session` | All authenticated app gateways/modules | Session token hash, tenant/app scope, user active | Authenticated actor context |
| `identity_access.require_app_scope` | App gateways/modules | Actor must match app/tenant scope | Success/failure only |
| `identity_access.get_user` | TenantApp, modules | Tenant Admin own tenant or module-owned reference | Safe user profile/status |
| `staff_access.require_staff_permission` | CashierApp, StationStaffApp, ServiceStaffApp, modules | Active role plus station/hall scope where relevant | Success/failure only |
| `staff_access.list_staff` | TenantApp | Tenant Admin own tenant | Staff profiles, roles, assignments |
| `staff_access.list_authorized_stations` | StationStaffApp, Preparation | Station Staff own tenant | Assigned active station IDs |
| `staff_access.list_authorized_halls` | ServiceStaffApp, Service Delivery | Service Staff own tenant | Assigned active hall IDs |
| `otp_messaging.get_challenge_state` | TenantApp, CashierApp, Identity and Access | Setup flow owns challenge | No OTP code |
| `otp_messaging.get_delivery_state` | Identity and Access, support/recovery | Tenant/admin or recovery scope | Redacted delivery attempts |

## Tenant Setup Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `venue_layout.create_hall` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Unique hall name/order |
| `venue_layout.update_hall` | TenantApp | Tenant Admin own tenant | Hall belongs to tenant |
| `venue_layout.disable_hall` | TenantApp | Tenant Admin own tenant | No unsafe active table/session dependency |
| `venue_layout.create_table` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Hall belongs to tenant; unique name/order |
| `venue_layout.update_table` | TenantApp | Tenant Admin own tenant | Table belongs to tenant |
| `venue_layout.disable_table` | TenantApp | Tenant Admin own tenant | No active TableSession |
| `station_setup.create_station` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Unique station name/order |
| `station_setup.update_station` | TenantApp | Tenant Admin own tenant | Station belongs to tenant |
| `station_setup.disable_station` | TenantApp | Tenant Admin own tenant | No active queue; no enabled products still routed there |
| `menu_catalog.create_category` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Unique category name/order |
| `menu_catalog.update_category` | TenantApp | Tenant Admin own tenant | Category belongs to tenant |
| `menu_catalog.disable_category` | TenantApp | Tenant Admin own tenant | History preserved |
| `menu_catalog.create_product_service` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Category/station same tenant; valid enabled variant |
| `menu_catalog.update_product_service` | TenantApp | Tenant Admin own tenant | No historical order snapshot rewrite |
| `menu_catalog.disable_product_service` | TenantApp | Tenant Admin own tenant | History preserved |
| `menu_catalog.manage_variant` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Non-negative price; one default variant |
| `menu_catalog.manage_modifiers` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Selection bounds valid |
| `menu_catalog.set_availability` | TenantApp | Tenant Admin own tenant | Target product/variant belongs to tenant |
| `table_display.create_claim` | TenantApp | Tenant Admin own tenant | Table belongs to tenant and is enabled |
| `table_display.consume_claim` | ESP32 setup flow | Valid raw claim secret | Claim unexpired/unconsumed |
| `table_display.revoke_credential` | TenantApp | Tenant Admin own tenant | Credential belongs to table/tenant |
| `table_display.rotate_credential` | TenantApp, claim consumption flow | Tenant Admin or valid claim flow | Old active credential revoked before new active credential |
| `tenant_operational_settings.update_settings` | TenantApp, Provisioning | Tenant Admin own tenant or Provisioning | Own tenant settings only; service tracking change audited |

## Tenant Setup Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `venue_layout.get_table_context` | CustomerApp, CashierApp, Ordering, Fulfillment | Customer/session or staff/internal scope | Table label, hall, enabled state only |
| `venue_layout.get_hall_table_board` | TenantApp, CashierApp | Tenant Admin or Cashier own tenant | Board plus derived state references |
| `venue_layout.list_halls` | TenantApp, Staff Access | Tenant Admin/internal staff assignment flow | Hall list |
| `station_setup.list_stations` | TenantApp, Menu Catalog, Staff Access | Tenant Admin or internal module scope | Station list |
| `station_setup.get_station_context` | StationStaffApp, CashierApp, Preparation | Station staff/cashier/internal scope | Station label/enabled state |
| `menu_catalog.list_menu_setup` | TenantApp | Tenant Admin own tenant | Full setup catalog for TenantApp menu management |
| `menu_catalog.get_product_service` | TenantApp, CashierApp, StationStaffApp | Tenant Admin, Cashier, or assigned station scope as appropriate | Product/service detail without changing price history |
| `menu_catalog.get_customer_menu` | CustomerApp | Tenant active; public/customer session context | Enabled/orderable/available customer menu |
| `menu_catalog.validate_cart_item` | Customer Ordering | Internal order/cart validation | Product/variant/modifier/station validity |
| `menu_catalog.price_cart_item` | Customer Ordering | Internal server-side pricing | Price snapshot inputs; ignores client price |
| `menu_catalog.read_order_item_routing` | Ordering, Fulfillment | Internal module scope | Routing and label snapshot inputs |
| `table_display.authenticate_credential` | ESP32 QR fetch flow, Table Presence | Raw display credential hash match | Trusted tenant/table display context |
| `table_display.get_display_state` | TenantApp | Tenant Admin own tenant | Claim/credential status without raw secrets |
| `tenant_operational_settings.get_settings` | TenantApp | Tenant Admin own tenant | Full tenant operational settings |
| `tenant_operational_settings.get_public_display_context` | TenantApp public page, Tenant Registry composition | Public-safe tenant route | Public display name fallback context |
| `tenant_operational_settings.is_service_delivery_tracking_enabled` | Fulfillment, ServiceStaffApp guards, CustomerApp/CashierApp visibility mapping | Internal or authenticated tenant-scoped caller | Boolean tracking mode |

## Ordering Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `table_presence.issue_current_qr_token` | ESP32 Table Display | Active display credential; tenant/table enabled | Token secret returned only in QR payload |
| `table_presence.redeem_token` | CustomerApp | Valid raw QR token | Token unexpired/unconsumed; atomic consume |
| `table_presence.expire_old_tokens` | Internal retention job | Internal operation | Must not break active display flow |
| `customer_ordering.attach_or_refresh_session` | Table Presence | Called only after QR redemption | Compatible session refreshed; cart preserved |
| `customer_ordering.add_or_update_cart_item` | CustomerApp | CustomerOrderingSession cookie | Menu item server-validated; client price ignored |
| `customer_ordering.remove_cart_item` | CustomerApp | CustomerOrderingSession cookie | Own active cart |
| `customer_ordering.submit_order` | CustomerApp | CustomerOrderingSession cookie plus idempotency key | Fresh presence, active cart, tenant/table active, menu revalidation |
| `customer_ordering.abandon_cart` | CustomerApp, retention job | Own session or retention policy | Cart is not billable |

## Ordering Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `table_presence.require_fresh_presence` | Customer Ordering, Settlement read guards | CustomerOrderingSession/table compatible | Success or fresh QR required |
| `table_presence.get_presence_state` | CustomerApp | Own customer session cookie | Presence expiry and table context |
| `customer_ordering.get_cart` | CustomerApp | Own customer session cookie | Active cart display state |
| `customer_ordering.list_my_orders` | CustomerApp | Own customer session cookie | Orders from same CustomerOrderingSession |
| `customer_ordering.list_table_orders` | CustomerApp, CashierApp | Customer fresh presence or Cashier role | Orders for active table session |
| `customer_ordering.read_order_item_routing` | StationStaffApp, ServiceStaffApp, Fulfillment | Staff/internal scope; station/hall enforced by Fulfillment | Order item snapshot/routing metadata |

## Fulfillment Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `preparation.create_queue_item` | Customer Ordering | Internal order transaction | One queue item per OrderItem; station enabled |
| `preparation.start_preparing` | StationStaffApp | Station Staff role and assigned station | Current status `pending` |
| `preparation.mark_ready` | StationStaffApp | Station Staff role and assigned station | Current status `preparing` |
| `preparation.report_cannot_prepare` | StationStaffApp | Station Staff role and assigned station | Current status `pending` or `preparing`; reason required |
| `service_delivery.mark_picked_up` | ServiceStaffApp | Service Staff role and assigned hall; service tracking enabled | PreparationItem is `ready` |
| `service_delivery.mark_delivered` | ServiceStaffApp | Service Staff role and assigned hall; service tracking enabled | Item is ready or picked up |
| `service_delivery.bulk_mark_delivered` | ServiceStaffApp | Service Staff role and assigned hall; service tracking enabled; idempotency key | All selected items belong to same table and are ready or picked up |

## Fulfillment Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `preparation.list_station_queue` | StationStaffApp | Station Staff role and assigned station | Queue for authorized station |
| `preparation.list_station_recent_items` | StationStaffApp | Station Staff role and assigned station | Same-day recent/completed items for authorized station |
| `preparation.read_preparation_state` | CustomerApp, CashierApp, ServiceStaffApp | Customer visibility, Cashier role, or Service Staff hall scope | Preparation state only |
| `preparation.get_station_workload` | StationStaffApp | Station Staff role and assigned station | Workload counters |
| `service_delivery.list_ready_items` | ServiceStaffApp | Service Staff role, assigned hall, tracking enabled | Ready/picked-up queue |
| `service_delivery.list_recent_deliveries` | ServiceStaffApp | Service Staff role, assigned hall, tracking enabled | Same-day delivered/recent activity for authorized halls |
| `service_delivery.read_delivery_state` | CustomerApp, CashierApp | Customer visibility or Cashier role | Customer sees mapped text only |
| `service_delivery.get_service_workload` | ServiceStaffApp | Service Staff role and assigned hall | Service workload counters |

## Settlement Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `table_session_billing.open_session_check_if_needed` | Customer Ordering | Internal order transaction | Tenant/table active; unique open TableSession |
| `table_session_billing.record_cashier_correction` | CashierApp | Cashier role own tenant; idempotency key | Reason required; target eligible under current release rules |
| `table_session_billing.close_session` | CashierApp | Cashier role own tenant | Check open; remaining balance zero |
| `payments.record_payment` | CashierApp | Cashier role own tenant | Check open; amount positive and not over remaining balance; idempotency key |
| `payments.void_payment` | CashierApp | Cashier role own tenant; idempotency key | Check open; non-provider current release payment; reason required |

## Settlement Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `table_session_billing.get_active_table_session` | CustomerApp, CashierApp, Ordering | Customer fresh presence, Cashier role, or internal order transaction | Active session or none |
| `table_session_billing.get_bill_summary` | CustomerApp, CashierApp | Customer fresh presence or Cashier role | Server-calculated total/paid/remaining |
| `table_session_billing.get_check` | CashierApp, Payments | Cashier role or internal settlement scope | Check/session state |
| `table_session_billing.list_cashier_corrections` | CashierApp | Cashier role | Correction history |
| `payments.list_payments` | CashierApp | Cashier role | Payment history for one Check/Adisyon |
| `payments.list_tenant_payments` | CashierApp | Cashier role own tenant | Current business-day tenant payment history |
| `payments.get_paid_amount` | Table Session and Billing | Internal settlement scope | Non-voided payment sum |
| `payments.get_customer_visible_summary` | CustomerApp | Fresh table presence | Read-only paid/remaining summary |
| `payments.get_payment_idempotency_result` | CashierApp/API layer | Cashier role and same request hash | Existing result or conflict |

## Governance Commands

| Contract | Allowed Caller | Required Scope Checks | Domain Guards |
| --- | --- | --- | --- |
| `audit.record_event` | Platform, Access, Tenant Setup, Ordering, Fulfillment, Settlement | Caller is owning module for the action | Action allowed; reason/metadata safe |
| `side_effects.enqueue_effect` | Modules after committed business decision | Owning module decided source action | Payload redacted; idempotencyRef stable |
| `side_effects.claim_next_effect` | Worker | Worker process only | Row-level claim |
| `side_effects.record_attempt` | Worker | Worker owns claimed message | Provider result redacted |
| `side_effects.mark_completed` | Worker | Worker owns claimed message | Successful attempt exists |
| `side_effects.mark_failed` | Worker | Worker owns claimed message | Retry policy applied |
| `side_effects.recover_stale_claims` | Worker, recovery tooling | Worker process or recovery authority | Claim lease expired |

## Governance Queries

| Contract | Allowed Caller | Required Scope Checks | Result Boundary |
| --- | --- | --- | --- |
| `audit.query_platform_audit` | PlatformApp | Platform Owner | Platform-visible audit |
| `audit.query_tenant_audit` | TenantApp | Tenant Admin own tenant | Tenant audit without platform-only secrets |
| `audit.query_operational_audit` | CashierApp, recovery tooling | Cashier role or recovery authority | Operational audit with redaction |
| `side_effects.get_effect_state` | Source module, recovery tooling | Owning module or recovery authority | Redacted outbox state |
| `side_effects.list_failed_effects` | Platform/recovery tooling | Platform Owner/recovery authority | Failed side effects with redacted attempts |

## CustomerApp Special Rules

CustomerApp does not use Identity and Access.

| Action | Required Guard |
| --- | --- |
| Browse public menu | Tenant active; menu item visibility rules |
| Create/refresh CustomerOrderingSession | Successful QR token redemption |
| Read own cart | Own CustomerOrderingSession cookie |
| Submit order | Own CustomerOrderingSession, fresh table presence, idempotency key, active cart |
| Read my orders | Own CustomerOrderingSession cookie |
| Read table orders/bill/balance | Fresh table presence for the table |
| Mutate payments, corrections, session closure, preparation, delivery, tenant setup | Never allowed in the current release |

## ESP32 Display Special Rules

The ESP32 table display is not a user.

| Action | Required Guard |
| --- | --- |
| Consume setup claim | Valid unexpired one-time claim |
| Fetch current QR | Active TableDisplayCredential |
| Identify table | Backend resolves tenant/table from credential |
| Submit orders or mutate tenant data | Never allowed |

## Cross-Role Limits

| Actor | Explicit Non-Authority |
| --- | --- |
| Platform Owner | Does not mutate tenant runtime orders, payments, preparation, delivery, or table sessions in normal current release flow. |
| Tenant Admin | Does not receive payments, close sessions, prepare station items, deliver items, or create customer orders. |
| Cashier | Does not configure tenant setup, create tenants, prepare items, or deliver items. |
| Station Staff | Does not change menu/setup, payments, delivery state, or session closure. |
| Service Staff | Does not prepare station items, change menu/setup, payments, or session closure. |
| Customer | Does not mutate submitted orders, payments, fulfillment state, setup, or session closure. |

## Revocation Rules

- Disabled users fail session validation.
- Revoked roles fail staff permission checks as soon as practical.
- Revoked station/hall assignments fail operation-specific scope checks.
- Suspended tenants block tenant runtime actions even if sessions remain technically present.
- Revoked display credentials cannot fetch QR payloads.
- Expired customer presence blocks submit/table-order/balance visibility but does not delete cart.

## Open Questions

None currently.
