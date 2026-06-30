# V1 Scenario Catalog

This catalog enumerates v1 app scenarios as happy paths and branches.

It is intentionally more detailed than the end-to-end flow. The goal is to make product behavior explicit before module design, database schema, API contracts, and UI implementation.

## Scope Rule

This file covers all v1-known branches for the six app surfaces:

- PlatformApp
- TenantApp
- CustomerApp
- StationStaffApp
- ServiceStaffApp
- CashierApp

When implementation discovers a new meaningful branch, it must be added here or explicitly rejected as out of scope before code, schema, or API behavior is finalized.

## Scenario Format

Each scenario uses this structure:

| Field | Meaning |
| --- | --- |
| Happy path | Expected normal path |
| Branches | Alternative or failure paths that must be handled |
| Result | State the system must reach |
| Ownership | App/context that owns the decision |

## Cross-App Master Scenario

### E2E-01: First Complete Table Visit

Happy path:

1. Platform Owner creates an active tenant.
2. Tenant Admin completes first login and reviews starter data.
3. Tenant Admin provisions the table display.
4. Customer scans the fresh table QR.
5. Customer builds and submits an order.
6. Station staff prepares assigned items.
7. Service staff delivers ready items when service tracking is enabled.
8. Cashier receives payment.
9. Cashier closes the TableSession.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant provisioning fails | Tenant remains `provisioning_failed`; no runtime app should behave as active |
| Table display not provisioned | Customer cannot obtain a valid QR from that table |
| QR is expired/used/wrong-table | Customer must scan current QR again |
| Fresh presence expires before submit | Cart is preserved; customer must re-scan current QR |
| Product becomes unavailable before submit | Submit is rejected for affected item; cart remains editable |
| Duplicate order submit | Original idempotent result is returned; no duplicate order |
| Station reports `cannot_prepare` | Item remains billable until cashier correction; cashier sees exception |
| Service tracking disabled | ServiceStaffApp has no queue; `ready` becomes final tracked fulfillment |
| Partial payment only | TableSession remains open with remaining balance |
| Full payment but cashier does not close | TableSession remains open until explicit close |
| Close requested twice | Second request returns already-closed result without mutation |

Ownership:

- Platform: tenant lifecycle and provisioning.
- Tenant Setup: halls, tables, stations, menu, staff, display provisioning.
- Ordering: QR presence, customer session, cart, order submission.
- Fulfillment: preparation and service delivery.
- Settlement: Check/Adisyon, payments, corrections, closure.
- Governance: audit.

## PlatformApp Scenarios

### P-01: Platform Owner Login

Happy path:

1. Platform Owner opens `https://platform.iotables.net/login`.
2. PlatformApp validates username/password.
3. If TOTP is enrolled, PlatformApp validates TOTP.
4. PlatformApp opens the dashboard.

Branches:

| Branch | Expected Result |
| --- | --- |
| First Platform Owner does not exist | Access is unavailable until explicit bootstrap command creates it |
| Bootstrap password still active | Force password change before dashboard access |
| TOTP not enrolled after first setup | Force TOTP enrollment before dashboard access |
| Invalid credentials | Reject without tenant data exposure |
| Invalid TOTP | Reject without tenant data exposure |
| Platform user disabled | Reject login |

Result:

- Dashboard is visible only to authenticated Platform Owner.

Ownership:

- PlatformApp + Access.

### P-02: Create Tenant With Cafe Starter

Happy path:

1. Platform Owner enters tenant name, subdomain, GSM number, and optional profile fields.
2. PlatformApp validates required fields and subdomain uniqueness.
3. PlatformApp creates Tenant in `provisioning`.
4. PlatformApp creates tenant admin and starter staff users.
5. Sector Starter Templates applies `cafe.v1` once.
6. Starter data creates halls, tables, stations, products, staff, and default service delivery tracking.
7. PlatformApp records `starter_template.applied`.
8. PlatformApp activates tenant after required setup records commit.

Branches:

| Branch | Expected Result |
| --- | --- |
| Required tenant name missing | Reject before provisioning starts |
| Required subdomain missing | Reject before provisioning starts |
| Required GSM missing | Reject before provisioning starts |
| Subdomain already exists | Reject before provisioning starts |
| Tenant name duplicates an existing tenant | Allowed only if subdomain is unique; name is not trusted identifier |
| Optional sector omitted | Create tenant without starter data unless PlatformApp requires sector selection later |
| Starter application already exists for tenant/template | Do not reapply starter data |
| Starter data transaction fails | Roll back or mark tenant `provisioning_failed`; do not activate |
| Tenant admin creation fails | Roll back or mark tenant `provisioning_failed`; do not activate |
| Audit write fails for critical creation event | Tenant creation must fail or enter recoverable failure according to audit failure policy |

Result:

- Active tenant exists with immutable name/subdomain and editable GSM.
- Starter data is normal tenant-owned data after creation.

Ownership:

- PlatformApp + Platform + Access + Sector Starter Templates + Governance.

### P-03: Manual DNS Readiness

Happy path:

1. Platform Owner manually creates DNS outside the app.
2. Platform Owner marks DNS readiness in PlatformApp.
3. Tenant health summary reflects DNS readiness.

Branches:

| Branch | Expected Result |
| --- | --- |
| DNS readiness not marked | Tenant may still be active internally, but PlatformApp health shows DNS not ready |
| Platform Owner marks readiness incorrectly | PlatformApp records the change; correction is another audited readiness update |

Result:

- DNS is tracked as a manual checklist state, not automated.

Ownership:

- PlatformApp + Platform.

### P-04: Suspend and Reactivate Tenant

Happy path:

1. Platform Owner opens Tenant Detail.
2. Platform Owner suspends tenant with reason.
3. Tenant runtime apps reject normal operation.
4. Platform Owner later reactivates tenant if allowed.

Branches:

| Branch | Expected Result |
| --- | --- |
| Suspend without reason | Reject |
| Tenant already suspended | Return current suspended state idempotently |
| Suspended tenant receives customer order request | Reject and show unavailable state |
| Suspended tenant receives staff/cashier request | Block runtime access |

Result:

- Tenant status controls runtime availability.

Ownership:

- PlatformApp + Platform + Governance.

### P-05: List and Inspect Tenants

Happy path:

1. Platform Owner opens dashboard or Tenant List.
2. PlatformApp lists tenants with identity, subdomain, lifecycle state, DNS readiness, setup state, and high-level health.
3. Platform Owner opens Tenant Detail.
4. PlatformApp shows platform-owned tenant metadata, lifecycle, setup state, starter template state, tenant admin bootstrap state, and audit summary.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant has no DNS readiness | Health shows DNS not ready |
| Tenant provisioning failed | Detail shows failure state and recovery affordance |
| Tenant suspended | Detail shows suspended state and reason/audit |
| Platform Owner attempts runtime mutation from detail | Reject unless explicit support/recovery workflow exists |
| Runtime health signal unavailable | Show unknown/degraded summary without blocking platform metadata view |

Result:

- PlatformApp can inspect platform-owned state without becoming a tenant runtime console.

Ownership:

- PlatformApp + Platform + Governance.

### P-06: Update Tenant GSM

Happy path:

1. Platform Owner or authorized TenantApp path opens editable tenant settings.
2. Actor updates tenant GSM number.
3. Backend validates format and tenant scope.
4. Backend records change and audit.
5. Future tenant admin/cashier OTP challenges use the new GSM.

Branches:

| Branch | Expected Result |
| --- | --- |
| GSM format invalid | Reject |
| Actor not authorized | Reject |
| Same GSM submitted | Return unchanged/idempotent result |
| Active OTP challenge exists for old GSM | Existing challenge should not silently change target; new challenge uses new GSM |

Result:

- Tenant GSM changes are explicit, audited, and affect future sensitive flows.

Ownership:

- PlatformApp or TenantApp + Platform/Tenant Registry + Governance.

## TenantApp Scenarios

### T-01: Public Tenant Page

Happy path:

1. Visitor opens `https://[tenant].iotables.net/`.
2. TenantApp resolves tenant by subdomain.
3. TenantApp shows safe public tenant fields.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant does not exist | Show not-found/unavailable page |
| Tenant is suspended | Show tenant unavailable |
| Tenant is provisioning/provisioning_failed | Do not expose admin/runtime details |
| Visitor attempts admin action from public page | Require login route |

Result:

- Public page never exposes staff, session, order, payment, setup checklist, or operational internals.

Ownership:

- TenantApp + Platform read.

### T-02: Tenant Admin First Login

Happy path:

1. Tenant Admin opens `/login`.
2. Tenant Admin enters username and temporary password.
3. TenantApp forces password change.
4. OTP SMS is sent to tenant GSM.
5. Tenant Admin verifies OTP.
6. TenantApp opens admin dashboard.

Branches:

| Branch | Expected Result |
| --- | --- |
| Invalid temporary password | Reject |
| Password change uses rejected password | Reject |
| OTP expired | Require new OTP challenge |
| OTP failed too many times | Lock/slow challenge according to OTP rules |
| Tenant GSM changed before verification | New challenge must use current tenant GSM |
| User already completed first login | Normal login path, no bootstrap password access |

Result:

- Tenant admin has a non-bootstrap credential and verified first setup.

Ownership:

- TenantApp + Access + OTP/Messaging.

### T-03: Configure Halls and Tables

Happy path:

1. Tenant Admin opens Hall Management.
2. Tenant Admin creates/edits halls.
3. Tenant Admin selects a hall.
4. Tenant Admin creates/edits/reorders/disables tables in the same workspace.
5. Selecting a table opens a contextual panel.

Branches:

| Branch | Expected Result |
| --- | --- |
| Hall name missing | Reject before save |
| Table name missing | Reject before save |
| Reorder request has duplicate order positions | Server normalizes or rejects according to implementation contract |
| Table has historical sessions/orders | Hard delete is unavailable; disable instead |
| Table has active TableSession | Disable must be blocked or require explicit recovery workflow; normal disable cannot strand an active session |
| Tenant Admin tries standalone table management page | Not a primary v1 page; use hall workspace/panel |

Result:

- Venue structure remains coherent and table history remains intact.

Ownership:

- TenantApp + Venue Layout + Governance.

### T-04: Provision Table Display

Happy path:

1. Tenant Admin opens a table detail panel.
2. TenantApp creates a short-lived one-time display claim.
3. ESP32 setup consumes the claim.
4. Backend returns display credential once.
5. Table panel shows provisioned display state.

Branches:

| Branch | Expected Result |
| --- | --- |
| Claim expires before use | Claim is rejected; Tenant Admin can create a new claim |
| Claim is reused | Reject |
| Claim belongs to another table | Reject |
| Table is disabled | Reject provisioning unless explicit recovery allows it |
| Table already has active credential | Re-provisioning revokes previous credential and creates a new active one |
| ESP32 loses credential | Tenant Admin re-provisions table display |

Result:

- One active display credential exists per tenant/table.

Ownership:

- TenantApp + Table Display Provisioning.

### T-05: Configure Service Delivery Tracking

Happy path:

1. Tenant Admin opens Tenant Settings.
2. Tenant Admin enables or disables service delivery tracking.
3. TenantApp records setting change and audit.
4. Staff apps adapt to the setting.

Branches:

| Branch | Expected Result |
| --- | --- |
| Enabled | ServiceStaffApp queue is available to authorized service staff |
| Disabled | ServiceStaffApp queue and mutation controls are hidden/blocked |
| Disabled while ready items exist | DeliveryState stops being required; `ready` is final tracked fulfillment from that point |
| Re-enabled later | New ready items can flow through ServiceStaffApp; historical disabled-mode items are not retroactively delivered |

Result:

- Customer-visible status semantics follow current service delivery tracking mode.

Ownership:

- TenantApp + Tenant Setup + Fulfillment read.

### T-06: Configure Menu and Station Routing

Happy path:

1. Tenant Admin creates categories.
2. Tenant Admin creates product/services.
3. Tenant Admin sets prices, descriptions, modifiers, availability, and one station assignment.
4. CustomerApp reads available menu.
5. Ordering validates cart against current menu at submit time.

Branches:

| Branch | Expected Result |
| --- | --- |
| Product has no station | Product cannot be orderable |
| Product has more than one station | Reject in v1 |
| Product disabled | Historical orders remain; product cannot be ordered |
| Product unavailable | Product may be visible but not orderable |
| Price changes | Existing OrderItem snapshots do not change |
| Required modifier missing | Cart item invalid |
| Modifier becomes unavailable before submit | Submit rejects affected item and preserves cart |

Result:

- Menu is the source for current orderability and pricing; order snapshots preserve history.

Ownership:

- TenantApp + Menu Catalog + Governance.

### T-07: Configure Stations

Happy path:

1. Tenant Admin opens Station Management.
2. Tenant Admin reviews starter stations.
3. Tenant Admin creates or edits station name and availability.
4. Tenant Admin disables stations no longer used.
5. Menu Catalog uses enabled stations for product/service assignment.

Branches:

| Branch | Expected Result |
| --- | --- |
| Station name missing | Reject |
| Station has active preparation items | Disable must be blocked or require explicit recovery/workflow |
| Product/service still routes to disabled station | Product/service cannot remain orderable until rerouted or disabled |
| Station staff assigned to disabled station | Assignment remains historical/configured but cannot grant active queue operations |

Result:

- Station setup remains compatible with menu routing and preparation queues.

Ownership:

- TenantApp + Tenant Setup + Menu Catalog/Fulfillment read + Governance.

### T-08: Configure Tenant Settings

Happy path:

1. Tenant Admin opens Tenant Settings.
2. Tenant Admin edits allowed mutable fields:
   - public display name,
   - GSM number,
   - address,
   - capacity,
   - sector classification,
   - service delivery tracking.
3. Backend validates tenant scope and immutable fields.
4. Backend records audit for sensitive/customer-visible changes.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant Admin edits tenant name | Reject |
| Tenant Admin edits subdomain | Reject |
| Sector changes after creation | Update classification only; do not rerun starter data |
| Capacity changes | Update informational field; no entitlement enforcement in v1 |
| Public display name omitted | Public page falls back to immutable tenant name |
| GSM changes | Audit and use new GSM for future OTP challenges |

Result:

- Tenant settings remain mutable only where v1 allows.

Ownership:

- TenantApp + Tenant Registry + Tenant Setup + Governance.

### T-09: Review Starter Data

Happy path:

1. Tenant Admin logs in after tenant creation.
2. TenantApp shows starter halls, tables, stations, menu items, staff, and service tracking setting as normal tenant data.
3. Tenant Admin edits, disables, deletes where allowed, or extends starter data.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant Admin deletes starter product before orders exist | Allowed if normal menu rules allow deletion/disable |
| Starter product has historical orders | Hard delete unavailable; disable/preserve history |
| Tenant Admin removes starter hall with active tables/sessions | Reject or require explicit recovery workflow |
| App restart/deploy occurs after edits | Starter data must not be recreated |
| New starter template version exists | Existing tenant does not receive it automatically |

Result:

- Starter data is not special after creation, and provisioning remains one-time.

Ownership:

- TenantApp + Sector Starter Templates read + Tenant Setup + Governance.

### T-10: Configure Staff Access

Happy path:

1. Tenant Admin creates or reviews staff users.
2. Tenant Admin assigns app roles.
3. Tenant Admin assigns station scopes for station staff.
4. Tenant Admin assigns hall scopes for service staff.
5. Staff apps enforce scopes server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| User has cashier role only | Can enter CashierApp only |
| User has station role without station scope | StationStaffApp shows no operational station access |
| User has service role without hall scope | ServiceStaffApp shows no operational hall access |
| User has multiple roles | Each app checks its own role and scope independently |
| User disabled | Existing sessions stop working as soon as practical |
| Tenant Admin changes scope while staff is active | Next action must enforce updated scope server-side |

Result:

- Staff access is tenant-scoped, app-scoped, and server-authorized.

Ownership:

- TenantApp + Staff Access + Access + Governance.

## CustomerApp Scenarios

### C-01: Redeem Fresh QR

Happy path:

1. Customer scans current QR.
2. CustomerApp submits TableAccessToken.
3. Backend validates token hash, expiry, tenant/table, and consumed state.
4. Backend consumes token atomically.
5. Backend creates or refreshes CustomerOrderingSession.
6. Backend sets `presenceValidUntil`.
7. CustomerApp opens menu.

Branches:

| Branch | Expected Result |
| --- | --- |
| Token expired | Ask customer to scan current QR |
| Token already consumed | Ask customer to scan current QR |
| Token belongs to another table | Reject and ask customer to scan own table QR |
| Tenant suspended | Show tenant unavailable |
| Table disabled | Reject ordering for table |
| Existing CustomerOrderingSession same tenant/table | Refresh same session |
| Existing CustomerOrderingSession another tenant/table | Do not silently transfer cart; require correct QR/session context |
| Browser rejects cookie | Customer may browse only if implementation allows stateless preview; ordering cannot proceed without server session |

Result:

- Customer has a valid anonymous session and fresh table presence.

Ownership:

- CustomerApp + Ordering / Table Presence.

### C-02: Browse Menu and Build Cart

Happy path:

1. Customer browses categories and products.
2. Customer opens product detail panel.
3. Customer selects required modifiers/options.
4. Customer adds item to cart.
5. Customer edits quantity, note, and modifiers before submission.

Branches:

| Branch | Expected Result |
| --- | --- |
| Product unavailable | Product is not orderable |
| Product disabled | Product is not orderable |
| Required modifier missing | Add-to-cart is blocked |
| Invalid modifier combination | Add-to-cart is blocked |
| Quantity invalid | Add-to-cart/update is blocked |
| Fresh presence expires while browsing | Browsing can continue; submit will require fresh QR |
| CustomerOrderingSession expires | Cart may be lost; fresh QR can create a new session |
| Browser refreshes page | Cart is restored while server session/cookie remains valid |

Result:

- Cart remains non-billable and owned by CustomerOrderingSession.

Ownership:

- CustomerApp + Customer Session and Cart + Menu Catalog read.

### C-03: Submit First Order at Empty Table

Happy path:

1. Customer submits cart with idempotency key.
2. Backend validates session, fresh presence, cart, menu, table, and tenant.
3. Backend creates new TableSession because no active session exists.
4. Backend creates one Check/Adisyon for the TableSession.
5. Backend creates Order, OrderItems, snapshots, and PreparationItems.
6. Backend commits transaction.
7. CustomerApp clears submitted cart and shows confirmation.

Branches:

| Branch | Expected Result |
| --- | --- |
| Fresh presence expired | Preserve cart and require fresh QR |
| Cart empty | Reject submit |
| Product unavailable at submit | Reject affected item and preserve cart |
| Modifier invalid at submit | Reject affected item and preserve cart |
| Table disabled at submit | Reject and preserve cart where useful |
| Tenant suspended at submit | Reject and show unavailable |
| Concurrent first order creates TableSession first | Use existing active TableSession or retry safely; never create two active sessions |
| Transaction fails after partial work | Roll back; no partial order visible |
| Duplicate idempotency key same request | Return original result |
| Duplicate idempotency key different request | Fail closed |

Result:

- One active TableSession, one Check, and one accepted order exist.

Ownership:

- CustomerApp + Ordering + Settlement command + Fulfillment.

### C-04: Submit Additional Order at Active Table

Happy path:

1. Customer scans fresh QR or still has fresh presence.
2. Customer builds another cart.
3. Backend attaches new order to current active TableSession.
4. My Orders shows all orders from that CustomerOrderingSession.
5. Table Orders shows all orders in active TableSession after fresh presence.

Branches:

| Branch | Expected Result |
| --- | --- |
| Same browser/session orders again | My Orders shows both orders |
| Different browser at same table orders | Order joins same TableSession; not shown in first browser's My Orders |
| Browser cookie deleted | My Orders from old session is lost; Table Orders can be shown after fresh QR |
| TableSession closes before submit | Require fresh QR and attach to current active/new TableSession only if table can accept orders |

Result:

- Multiple CustomerOrderingSessions may contribute orders to one TableSession.

Ownership:

- CustomerApp + Ordering + Settlement.

### C-05: View My Orders, Table Orders, and Bill

Happy path:

1. Customer opens My Orders.
2. CustomerApp shows orders from current CustomerOrderingSession.
3. Customer verifies fresh presence for Table Orders or bill.
4. CustomerApp shows active TableSession orders and read-only bill/balance.

Branches:

| Branch | Expected Result |
| --- | --- |
| Fresh presence missing for Table Orders | Ask customer to scan current QR |
| Cookie lost | My Orders may be lost; Table Orders can recover after fresh QR |
| TableSession closed | Current customer cannot mutate it; new order requires fresh QR and current table state |
| Payment recorded by cashier | Bill/balance updates read-only |
| Payment voided by cashier | Bill/balance updates read-only |
| Item voided by cashier | Order/bill state updates read-only |

Result:

- Customer can inspect but not mutate billing or submitted orders.

Ownership:

- CustomerApp + Ordering read + Settlement read.

## StationStaffApp Scenarios

### S-01: Station Staff Login and Queue Entry

Happy path:

1. Staff opens StationStaffApp.
2. Staff logs in.
3. Bootstrap password change is forced if needed.
4. If one station is authorized, queue opens.
5. If multiple stations are authorized, station selector opens.

Branches:

| Branch | Expected Result |
| --- | --- |
| Invalid credentials | Reject |
| User disabled | Reject |
| User lacks station_staff role | Reject app access |
| User has no authorized stations | Show no station access state |
| Station disabled after login | Next queue/action must fail or remove station from selection |

Result:

- Staff sees only authorized station queues.

Ownership:

- StationStaffApp + Access + Staff Access.

### S-02: Start Preparing Item

Happy path:

1. Staff selects a `pending` item.
2. Staff marks it `preparing`.
3. Backend validates station authorization and current state.
4. Backend records transition and actor.

Branches:

| Branch | Expected Result |
| --- | --- |
| Item not in authorized station | Reject |
| Item already `preparing` by same or another actor | Return current state idempotently or reject as stale according to API contract |
| Item already `ready` | Reject stale transition |
| Item `cannot_prepare` | Reject normal preparation transition |
| TableSession closed | Reject except explicit recovery |
| Duplicate click | No duplicate transition corruption |

Result:

- Preparation state is correct and auditable.

Ownership:

- StationStaffApp + Preparation.

### S-03: Mark Item Ready

Happy path:

1. Staff selects a `preparing` item.
2. Staff marks it `ready`.
3. Backend validates current state and station authorization.
4. Ready item becomes visible to ServiceStaffApp if service tracking is enabled.

Branches:

| Branch | Expected Result |
| --- | --- |
| Item still `pending` | Reject direct ready transition unless an explicit shortcut is later introduced |
| Item already `ready` | Return current state idempotently or reject as stale |
| Service tracking enabled | CustomerApp still shows `Hazırlanıyor`; ServiceStaffApp can deliver |
| Service tracking disabled | CustomerApp shows `Teslim edildi`; no delivery state is created |
| Duplicate click | No duplicate transition corruption |

Result:

- Station work is complete.

Ownership:

- StationStaffApp + Preparation + Service Delivery read.

### S-04: Report Cannot Prepare

Happy path:

1. Staff selects `pending` or `preparing` item.
2. Staff enters required reason.
3. Backend validates current state and authorization.
4. Backend records `cannot_prepare` and actor.
5. CashierApp sees exception.

Branches:

| Branch | Expected Result |
| --- | --- |
| Reason missing | Reject |
| Item already `ready` | Reject |
| Item already `picked_up`/`delivered` | Reject |
| Unauthorized station | Reject |
| Cashier later voids item | Item/bill state updates through cashier correction, not StationStaffApp |

Result:

- Operational exception is visible without financial mutation.

Ownership:

- StationStaffApp + Preparation + CashierApp read.

## ServiceStaffApp Scenarios

### SV-01: Service Staff Login and Queue Entry

Happy path:

1. Staff opens ServiceStaffApp.
2. Staff logs in.
3. Bootstrap password change is forced if needed.
4. Backend checks service delivery tracking setting.
5. If enabled, authorized hall queue opens.

Branches:

| Branch | Expected Result |
| --- | --- |
| Service delivery tracking disabled | No operational queue or delivery controls |
| User lacks service_staff role | Reject app access |
| User has no authorized halls | Show no hall access state |
| Hall disabled after login | Remove/deny affected hall operations |

Result:

- Service controls exist only when tenant setting and staff scope allow them.

Ownership:

- ServiceStaffApp + Access + Staff Access + Service Delivery.

### SV-02: Pick Up Item

Happy path:

1. Staff selects a ready item in authorized hall.
2. Staff marks it `picked_up`.
3. Backend validates readiness, hall scope, and current delivery state.
4. CustomerApp still shows `Hazırlanıyor`.

Branches:

| Branch | Expected Result |
| --- | --- |
| Item not ready | Reject |
| Item unauthorized hall | Reject |
| Item already picked up | Return current state idempotently or reject stale command |
| Item already delivered | Reject stale command |
| Service tracking disabled | Reject |

Result:

- Item is in delivery progress.

Ownership:

- ServiceStaffApp + Service Delivery.

### SV-03: Mark Delivered

Happy path:

1. Staff selects ready or picked-up item.
2. Staff marks delivered.
3. Backend validates state and hall authorization.
4. CustomerApp maps item to `Teslim edildi`.

Branches:

| Branch | Expected Result |
| --- | --- |
| Ready item delivered without picked_up | Allowed |
| Picked-up item delivered | Allowed |
| Pending/preparing item delivered | Reject |
| Unauthorized hall | Reject |
| Duplicate delivered command | Return delivered state idempotently |
| Closed TableSession | Reject except explicit recovery |

Result:

- Item has delivery proof.

Ownership:

- ServiceStaffApp + Service Delivery.

### SV-04: Bulk Deliver Same Table Items

Happy path:

1. Staff selects multiple ready/picked-up items on the same table.
2. Staff marks delivered with one idempotency key.
3. Backend validates every item.
4. Backend records transitions with one actor.

Branches:

| Branch | Expected Result |
| --- | --- |
| Items from multiple tables | Reject bulk action |
| One selected item invalid | Reject whole bulk command; do not partially deliver |
| Duplicate bulk command | Return original idempotent result |
| One item already delivered | Return current result only if idempotency proves same command; otherwise reject stale selection |

Result:

- Bulk delivery remains atomic and same-table only.

Ownership:

- ServiceStaffApp + Service Delivery.

## CashierApp Scenarios

### K-01: Cashier First Login

Happy path:

1. Cashier opens CashierApp login.
2. Cashier enters bootstrap credentials.
3. Cashier changes password.
4. OTP SMS is sent to tenant GSM.
5. Cashier verifies OTP.
6. Cashier workspace opens.

Branches:

| Branch | Expected Result |
| --- | --- |
| Invalid credentials | Reject |
| OTP expired | Require new OTP |
| OTP verification fails too often | Lock/slow challenge |
| User lacks cashier role | Reject app access |
| User disabled | Reject |

Result:

- Cashier has secure first-login setup.

Ownership:

- CashierApp + Access + OTP/Messaging.

### K-02: Monitor and Inspect Active Session

Happy path:

1. Cashier opens workspace.
2. Cashier sees halls, tables, active session state, latest item state, total, paid, remaining.
3. Cashier selects active table.
4. Session panel opens with orders, items, Check/Adisyon, payments, and corrections.

Branches:

| Branch | Expected Result |
| --- | --- |
| Table has no active session | Show empty/available table state |
| Table session changes while panel open | Panel refreshes or stale action is rejected server-side |
| Service tracking disabled | Fulfillment state uses `ready` as final tracked state |
| Item `cannot_prepare` exists | Highlight cashier attention state |

Result:

- Cashier has operational context without leaving table board.

Ownership:

- CashierApp + Settlement read + Ordering/Fulfillment read.

### K-03: Record Partial Payment

Happy path:

1. Cashier opens active Check.
2. Cashier enters payment amount less than remaining balance.
3. Cashier selects method: `cash`, `card`, or `transfer`.
4. Backend validates amount and idempotency key.
5. Backend records payment against Check.
6. Remaining balance decreases.
7. TableSession remains open.

Branches:

| Branch | Expected Result |
| --- | --- |
| Amount is zero/negative | Reject |
| Amount exceeds remaining balance | Reject in v1 |
| Duplicate submit same key | Return original payment |
| Same key different request | Fail closed |
| Check closed | Reject |
| Cashier lacks permission | Reject |

Result:

- Payment is recorded once and balance is server-calculated.

Ownership:

- CashierApp + Payments + Settlement.

### K-04: Record Full Payment and Close Session

Happy path:

1. Cashier records remaining balance as payment.
2. Remaining balance becomes zero.
3. Cashier explicitly closes TableSession.
4. Backend validates zero balance.
5. Backend closes Check and TableSession in one transaction.
6. Table becomes available for future session.

Branches:

| Branch | Expected Result |
| --- | --- |
| Balance remains above zero | Close is rejected |
| Close clicked twice | Return already closed state idempotently |
| New order arrives during close | Transaction/concurrency control prevents order attaching to closed session |
| Payment recorded concurrently by another cashier | Balance is recalculated server-side before close |
| Check already closed | Return closed state or reject stale command without mutation |

Result:

- Settlement is complete and table can accept a future session.

Ownership:

- CashierApp + Settlement + Payments.

### K-05: Add Cashier Note Correction

Happy path:

1. Cashier opens active session.
2. Cashier adds internal correction note with reason.
3. Backend records CashierCorrection and audit.

Branches:

| Branch | Expected Result |
| --- | --- |
| Reason missing | Reject |
| Session closed | Reject except explicit recovery |
| Duplicate submit | Return original correction by idempotency key |

Result:

- Note is auditable and does not mutate billable records.

Ownership:

- CashierApp + Settlement + Governance.

### K-06: Void Order Item

Happy path:

1. Cashier selects item in `pending` or `cannot_prepare`.
2. Cashier enters reason.
3. Backend verifies no payment has been recorded for the Check.
4. Backend records item void and CashierCorrection.
5. Bill summary recalculates server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| Item is `preparing`, `ready`, `picked_up`, or `delivered` | Reject in v1 |
| Any payment exists on Check | Reject item void in v1 |
| Reason missing | Reject |
| Item already voided | Return current state idempotently or reject stale request |
| Station attempts to void | Not allowed; only CashierApp correction can void |

Result:

- Item is voided through controlled cashier correction.

Ownership:

- CashierApp + Settlement + Ordering read + Preparation read.

### K-07: Void Payment

Happy path:

1. Cashier selects recorded non-provider payment on open Check.
2. Cashier enters reason.
3. Backend records payment void and audit.
4. Bill summary recalculates server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| Payment belongs to closed Check | Reject in v1 |
| Payment already voided | Return current state idempotently or reject stale request |
| External provider payment | Out of v1; reject if somehow present |
| Reason missing | Reject |

Result:

- Payment no longer counts toward paid amount.

Ownership:

- CashierApp + Payments + Settlement + Governance.

### K-08: View Payment History

Happy path:

1. Cashier opens Payment History.
2. CashierApp shows current business-day payment records visible to the cashier.
3. Cashier can inspect payment method, amount, actor, time, and void state.

Branches:

| Branch | Expected Result |
| --- | --- |
| No payments today | Show empty state |
| Payment was voided | Show void state and reason |
| Cashier requests arbitrary historical report | Out of v1 unless reporting workspace is introduced |
| Tenant has multiple cashiers | Show actor per payment; do not assume single cashier |

Result:

- Payment History supports operational review without becoming a full reporting module.

Ownership:

- CashierApp + Payments + Governance.

## Out-of-Scope Scenario Requests

These requests must not be implemented as hidden branches in v1:

| Request | V1 Result |
| --- | --- |
| Customer pays from CustomerApp | Out of scope |
| Customer cancels submitted order | Out of scope; staff/cashier correction only |
| Waiter enters an order | Out of scope |
| Split one table into multiple checks | Out of scope |
| Split payment by item/person | Out of scope |
| Move item between checks/sessions | Out of scope |
| Manual cashier item | Out of scope |
| Manual discount/service fee | Out of scope |
| Fiscal/e-Adisyon/ÖKC receipt issuance | Out of scope |
| Printer/cash drawer/payment terminal integration | Out of scope |
| Pickup/package/courier/phone/marketplace/counter-sale | Out of scope |
| Tenant multi-location | Out of scope |
| Offline-first POS | Out of scope |

## Branch Coverage Checklist

Before API contracts are finalized, each v1 endpoint or command should map to at least one scenario above and explicitly declare:

- happy path;
- invalid input branch;
- unauthorized branch;
- stale state branch;
- duplicate/idempotent retry branch where applicable;
- concurrent mutation branch where applicable;
- transaction failure behavior where applicable;
- visible app outcome.
