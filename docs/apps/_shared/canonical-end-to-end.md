# Current Release End-to-End App Flow

This document defines the expected current release behavior across the six IoTables apps.

It is the product behavior bridge between app docs and module/schema/API design. If a module, schema, or API conflicts with this flow, the app behavior wins unless the app docs are explicitly revised.

Detailed app-specific branch behavior lives in each app folder's `scenarios.md`. This file keeps the shared end-to-end path readable.

## Scope

The current release supports one restaurant/location per tenant and dine-in QR ordering only.

Included apps:

- PlatformApp
- TenantApp
- CustomerApp
- StationStaffApp
- ServiceStaffApp
- CashierApp

The current release excludes customer payment, waiter-entered orders, pickup/package/courier/phone/marketplace/counter-sale channels, fiscal/e-Adisyon/ÖKC document creation, hardware printer/cash drawer/payment terminal integrations, stock/recipe, multi-location, and offline-first POS.

## Main Happy Path

### 1. Platform Owner Creates Tenant

1. Platform Owner logs into PlatformApp.
2. Platform Owner creates a tenant with required identity:
   - tenant name,
   - tenant subdomain,
   - tenant GSM number.
3. PlatformApp submits the create-tenant command to Provisioning.
4. Provisioning registers the tenant in `provisioning` state.
5. Provisioning creates the first tenant admin through Access:
   - username: tenant subdomain,
   - temporary password: `admin`,
   - first password setup requires OTP SMS to tenant GSM.
6. Provisioning applies the selected sector starter template exactly once.
7. Governance records starter template completion.
8. Provisioning moves tenant to `active` after required setup records commit.
9. Tenant host availability relies on the environment wildcard DNS namespace that was configured during deployment.

Acceptance criteria:

- Tenant name and subdomain cannot be changed after creation.
- Tenant GSM is editable but audited.
- Starter data does not rerun after restart, deployment, migration, release upgrade, or tenant edit.
- Failed provisioning leaves a recoverable `provisioning_failed` state instead of partial silent success.
- PlatformApp does not expose a tenant-level DNS state; missing wildcard DNS is an environment/deployment fault.

### 2. Tenant Admin Configures Operation

1. Tenant Admin opens `https://[tenant].iotables.net/login`.
2. Tenant Admin changes the temporary password and verifies OTP.
3. TenantApp opens the admin workspace.
4. Tenant Admin reviews starter halls, tables, stations, products, staff, and settings.
5. Tenant Admin manages halls and tables from Hall Management.
6. Tenant Admin provisions table displays from table detail panels.
7. Tenant Admin manages stations and menu.
8. Tenant Admin assigns staff roles, station scopes, and service hall scopes.
9. Tenant Admin chooses whether service delivery tracking remains enabled.

Acceptance criteria:

- Tables are managed inside hall context, not as a primary standalone page.
- Each product/service routes to exactly one station in the current release.
- Service delivery tracking is enabled by default for the cafe starter.
- If service delivery tracking is disabled, ServiceStaffApp controls are hidden and `PreparationItem.ready` becomes the final tracked fulfillment state.
- TenantApp cannot edit tenant name or subdomain.

### 3. Table Display Shows Fresh QR

1. Tenant Admin creates a one-time table display claim for a table.
2. ESP32 setup submits the claim.
3. Backend consumes the claim atomically.
4. Backend returns a table display credential once.
5. ESP32 stores the credential locally.
6. ESP32 authenticates with the credential to fetch current QR payloads.
7. Backend resolves tenant/table from the credential.
8. QR token changes at least every 60 seconds and also rotates after redemption.

Acceptance criteria:

- ESP32 is a table display surface, not a separate device inventory aggregate in the current release.
- Only one active display credential exists per tenant/table.
- Re-provisioning revokes the previous active credential.
- Raw display credentials are never embedded in customer QR payloads.
- Client-sent table IDs are not trusted.

### 4. Customer Scans QR and Builds Cart

1. Customer scans the current QR on the table display.
2. CustomerApp redeems the TableAccessToken.
3. Backend atomically consumes the token.
4. Backend creates or refreshes a compatible CustomerOrderingSession.
5. Backend sets fresh table presence for 2 minutes.
6. Customer browses the menu and builds a cart.
7. Cart belongs to CustomerOrderingSession, not TableSession.

Acceptance criteria:

- Reused, expired, wrong-table, or already consumed QR tokens fail closed.
- A fresh QR refreshes an existing compatible CustomerOrderingSession when possible.
- CustomerOrderingSession can submit multiple orders while valid.
- Menu browsing can continue after fresh presence expires, but order submission cannot.
- Cart survives fresh QR re-verification while the CustomerOrderingSession remains recoverable.

### 5. Customer Submits Order

1. Customer taps order submit.
2. Frontend sends cart with an idempotency key.
3. Backend validates CustomerOrderingSession, tenant, table, fresh presence, cart, products, variants, modifiers, availability, and quantities.
4. Backend recalculates prices server-side.
5. Backend opens or selects the active TableSession and single Check/Adisyon through Settlement.
6. Backend joins CustomerOrderingSession to the current TableSession.
7. Backend creates Order and OrderItems with product/variant/price/modifier/station snapshots.
8. Backend creates PreparationItems for station queues.
9. Backend commits all order submission records in one transaction.
10. CustomerApp clears only the submitted cart and shows confirmation.

Acceptance criteria:

- Duplicate submit with the same idempotency key does not create duplicate orders.
- Failed order submission preserves the cart.
- No partial order appears in station, service, cashier, or customer history.
- Frontend prices and totals are informational only.
- The current release has no separate customer price-confirmation step.
- CustomerApp cannot modify or cancel submitted orders.

### 6. Station Staff Prepares Items

1. Station staff logs into StationStaffApp.
2. If assigned to one station, the station queue opens directly.
3. If assigned to multiple stations, station selection opens first.
4. Staff sees authorized station items grouped by preparation status and sorted oldest first.
5. Staff moves items from `pending` to `preparing`.
6. Staff marks prepared items `ready`, or marks impossible items `cannot_prepare` with a reason.

Acceptance criteria:

- Station staff cannot see or update unauthorized stations.
- Status transitions validate current state server-side.
- `cannot_prepare` requires a reason and actor.
- `cannot_prepare` does not cancel, refund, discount, reprice, close session, or remove billable records.
- CashierApp can see `cannot_prepare`.

### 7. Service Staff Delivers Items

When service delivery tracking is enabled:

1. Service staff logs into ServiceStaffApp.
2. Staff sees ready items for authorized halls.
3. Items are grouped by table and sorted by oldest ready item inside each table group.
4. Staff may mark an item `picked_up`.
5. Staff marks item `delivered`.
6. CustomerApp maps delivered items to `Teslim edildi`.

When service delivery tracking is disabled:

1. ServiceStaffApp exposes no operational queue.
2. DeliveryState does not run.
3. `PreparationItem.ready` is the final tracked fulfillment state.
4. CustomerApp maps `ready` to `Teslim edildi`.

Acceptance criteria:

- Service staff cannot operate unauthorized halls.
- Delivery commands fail closed when service delivery tracking is disabled.
- Bulk delivery is allowed only for selected items on the same table.
- Bulk delivery is idempotent and validates every selected item server-side.

### 8. Customer Views Orders and Bill

1. CustomerApp shows My Orders from the current CustomerOrderingSession.
2. CustomerApp can show Table Orders for the active TableSession after fresh presence verification.
3. CustomerApp can show read-only bill/balance summary after fresh presence verification.
4. CustomerApp cannot create payments, close sessions, discount, cancel, refund, or mutate billable records.

Acceptance criteria:

- My Orders shows all orders submitted by the same CustomerOrderingSession.
- Table Orders can recover visibility after cookie loss only through fresh QR presence.
- Bill and balance are calculated server-side.
- Customer-visible status depends on service delivery tracking mode.

### 9. Cashier Settles and Closes Session

1. Cashier logs into CashierApp.
2. First cashier password setup requires OTP to tenant GSM.
3. Cashier sees halls, tables, active sessions, balances, and latest order state.
4. Cashier opens a table session panel.
5. Cashier receives partial or full payments against the single Check/Adisyon.
6. Payments are amount-based only.
7. Cashier may apply only allowed current release corrections.
8. When remaining balance is zero, Cashier explicitly closes the TableSession.
9. The table becomes available for a future session.

Acceptance criteria:

- The current release has exactly one Check/Adisyon per TableSession.
- Split checks, merge checks, item/person-based split payment, item move, and customer payment are out of the current release.
- Payment creation and session closure are idempotent.
- Session closure is explicit; zero balance alone does not silently close.
- Closed sessions do not accept new orders, payments, or corrections except explicit recovery workflows.

## Allowed Cashier Corrections

The current release allows:

- internal cashier note on active TableSession/Check;
- order item void only while preparation state is `pending` or `cannot_prepare` and before any payment has been recorded for the Check;
- non-provider payment void only on an open Check.

The current release does not allow:

- manual order items;
- manual discounts;
- service fees;
- refunds after session closure;
- cancellation of items already `preparing`, `ready`, `picked_up`, or `delivered`;
- direct price snapshot edits;
- moving items between checks or sessions.

All corrections require cashier permission, reason, idempotency, server-side target validation, and audit.

## Failure and Recovery Rules

| Failure | Expected Behavior |
| --- | --- |
| Tenant provisioning fails | Tenant becomes `provisioning_failed`; no silent partial activation |
| Starter template was already applied | Do not apply again |
| QR token expired/used | Ask customer to scan current QR |
| Fresh presence expired | Preserve cart and require fresh QR before submit |
| Product unavailable | Reject affected item and keep cart editable |
| Order submit duplicated | Return original idempotent result |
| Order submit fails mid-transaction | No partial order is visible |
| Station cannot prepare item | Record `cannot_prepare`; cashier handles correction |
| Service tracking disabled | ServiceStaffApp controls hidden; `ready` is final tracked fulfillment |
| Payment submit duplicated | Return original idempotent result |
| Close session duplicated | Return already-closed result without mutation |

## Done for Current Release Behavior Definition

This flow is sufficiently defined for module, schema, and API design when:

- every app action maps to exactly one owning context or explicit cross-context command;
- every critical operation has idempotency and transaction expectations;
- every customer/staff/cashier-visible state has a defined source;
- every current release exclusion is explicit;
- app docs and this flow do not conflict.
