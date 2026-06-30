# V1 UI State Catalog

This catalog defines the required UI states for each IoTables v1 app.

It is not visual design. It defines the behavioral states the UI must support before detailed screen design, API contracts, and error response contracts are finalized.

## Global UI Rules

- Admin and operational apps should use few stable pages with contextual panels, drawers, dialogs, and inline controls.
- A primary page should exist only for a durable workspace.
- Secondary entity detail should usually open in context.
- Loading, empty, error, blocked, stale, success, and retry states must be explicit for every primary workspace.
- Frontend state must never be the only enforcement layer. UI affordances may prevent bad actions, but backend and database rules remain authoritative.
- Error copy must be user-facing, short, and action-oriented. It must not expose token values, internal IDs, stack traces, provider secrets, or security internals.
- Destructive, financial, access, and irreversible actions require explicit confirmation or a clearly scoped command surface.
- Duplicate-submit prevention must exist in UI, but idempotency remains backend-owned.

## PlatformApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, TOTP required, TOTP invalid, first password change required, TOTP enrollment required |
| Dashboard / Tenant List | loading, empty tenant list, partial health unavailable, tenant row stale, platform auth expired |
| Create Tenant | pristine, validating, submitting, provisioning, provisioning failed, success |
| Tenant Detail | loading, not found, suspended, provisioning, provisioning failed, DNS not ready, health unavailable |
| Tenant Audit | loading, empty audit, filtered empty, access denied |

### Empty States

- Tenant List empty: show that no tenant exists yet and expose Create Tenant.
- Tenant Audit empty: show that no platform-level audit events exist for the selected tenant.
- Tenant health unavailable: show unknown/degraded health without blocking platform metadata access.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| Platform Owner not authenticated | Redirect to login |
| Bootstrap user missing | Show setup unavailable state; do not expose dashboard |
| TOTP not enrolled | Force enrollment before dashboard |
| Tenant create required field missing | Mark field and keep form data |
| Subdomain already exists | Mark subdomain field and block submit |
| Provisioning failed | Show recoverable failure state and audit/retry affordance when available |
| DNS not ready | Show checklist warning, not a runtime mutation |
| Tenant suspended | Show suspended badge and reason where allowed |

### Success and Confirmation States

- Tenant creation success shows tenant identity, subdomain, lifecycle state, starter template state, admin bootstrap state, and DNS checklist.
- Tenant suspension/reactivation requires reason and shows updated lifecycle state after success.
- Tenant GSM update success shows audited sensitive-contact update.

### Stale and Retry States

- If tenant state changes while Tenant Detail is open, refresh visible lifecycle and setup state before allowing another lifecycle command.
- Retrying failed provisioning must use explicit recovery tooling, not normal Create Tenant submit.
- Duplicate Create Tenant submit should stay disabled while pending; backend uniqueness remains authoritative.

### Visual Priority Rules

- Tenant lifecycle state must be visible in tenant lists and details.
- `provisioning_failed`, `suspended`, and DNS-not-ready states need stronger visual priority than normal `active` state.
- Tenant health summary must not visually imply unsupported runtime control.

### Copy Requirements

- Use "tenant unavailable", "setup failed", "DNS not ready", and "provisioning" language.
- Do not claim DNS automation in v1.
- Do not present tenant as a fiscal/POS-complete system.

## TenantApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Public Tenant Page | loading, tenant not found, tenant unavailable, public info empty/fallback |
| Tenant Login | loading, invalid credentials, first password change required, OTP required, OTP expired, OTP failed |
| Admin Dashboard | loading, starter data present, setup incomplete, tenant suspended/blocked |
| Hall Management | loading, empty halls, selected hall empty tables, table panel loading, table active-session blocked |
| Station Management | loading, empty stations, station disabled, station has active items blocked |
| Menu Management | loading, empty categories, empty category products, invalid product, unavailable product, disabled product |
| Tenant Settings | loading, immutable field blocked, service tracking changed, GSM changed |
| Staff Management | loading, empty staff, disabled user, missing role/scope, active session permission changed |

### Empty States

- Empty halls: expose Create Hall.
- Hall without tables: expose Create Table inside hall context.
- Empty stations: expose Create Station before menu products can become orderable.
- Empty menu category: expose Create Product/Service.
- Empty staff list: expose Create Staff User, while preserving starter staff if present.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| Tenant not active | Block admin/runtime surfaces according to tenant state |
| Tenant admin first login incomplete | Force password change and OTP flow |
| OTP expired | Allow new OTP challenge |
| Tenant name/subdomain edit attempted | Show immutable field state and prevent edit |
| Table has active TableSession | Block normal disable/delete; require explicit recovery workflow if later added |
| Product has no station | Product cannot be orderable |
| Product assigned to disabled station | Product cannot remain orderable |
| Product has more than one station | Reject in v1 |
| Service tracking disabled | Hide ServiceStaffApp controls and explain ready-as-final operational mode |
| Staff user lacks scope | Show no operational scope warning for affected app role |

### Success and Confirmation States

- Halls/tables save in context without leaving Hall Management.
- Table display provisioning shows claim created, waiting for device, provisioned, revoked/re-provisioned states.
- Menu save shows product availability/orderability state.
- Service delivery tracking change shows immediate impact on ServiceStaffApp and customer-visible status semantics.
- Staff scope changes show which apps the user can access.

### Stale and Retry States

- If a table/session state changes while table panel is open, disable stale destructive actions and refresh.
- If station/product availability changes during edit, save must revalidate server-side and show field-level conflicts.
- If staff permission changes while user is active, next action must enforce updated scope; UI should refresh scope state when detected.

### Visual Priority Rules

- Hall/table management should keep selected hall and table context visible while panels are open.
- Disabled records must be visually distinct from orderable/active records.
- Service delivery tracking disabled mode must be visible in settings and not hidden as a minor toggle.
- Product orderability state must be clear when station, availability, or required modifier setup blocks ordering.

### Copy Requirements

- Use "disabled" for historical records that remain for integrity.
- Use "unavailable" for temporarily not orderable products/stations.
- Do not imply starter data is protected system data after creation.
- Do not expose platform setup internals on the public tenant page.

## CustomerApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| QR Entry / Session Start | loading, QR expired, QR already used, wrong table, tenant unavailable, table unavailable |
| Menu | loading, empty menu, category empty, product unavailable, image missing fallback |
| Product Detail | loading, required modifier missing, invalid combination, unavailable option |
| Cart | empty cart, editable cart, stale item, invalid item, fresh presence expired, submitting |
| Order Confirmation | accepted, duplicate submit returned, submit failed preserving cart |
| My Orders | loading, empty, session expired/lost |
| Table Orders | fresh presence required, loading, empty active session, active orders visible |
| Bill / Balance | fresh presence required, loading, read-only balance, payment updated |

### Empty States

- Empty menu: show no orderable items without exposing admin configuration.
- Empty cart: keep customer in menu context.
- My Orders empty: show no orders from this browser/session.
- Table Orders empty: show no active table orders after fresh QR verification.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| QR expired or already used | Ask customer to scan current QR |
| QR belongs to another table | Ask customer to scan the QR on their own table |
| Fresh presence expired before submit | Preserve cart and require current QR |
| CustomerOrderingSession expired | Create/refresh after valid QR; cart may be lost |
| Product unavailable at submit | Keep cart editable and highlight affected item |
| Modifier invalid at submit | Open affected item editor |
| Tenant suspended | Show tenant unavailable |
| Table disabled or closed to ordering | Reject order and preserve cart where useful |
| Duplicate submit | Show original accepted result, not a second order |
| Network failure after submit | Retry with same idempotency key and avoid duplicate order |

### Success and Confirmation States

- Successful QR redemption opens menu with table context.
- Successful add-to-cart keeps customer in menu/detail context.
- Successful order submit clears only submitted cart and shows order summary.
- Repeat order returns customer to menu and requires fresh presence again at submit.

### Stale and Retry States

- Menu data can become stale; submit must revalidate and return item-level correction states.
- TableSession can close before submit; CustomerApp must require fresh QR and attach only to current valid table state.
- Cookie loss removes My Orders continuity, but Table Orders can recover after fresh QR.

### Visual Priority Rules

- Current table context must be visible without exposing trusted table IDs.
- Cart submit readiness must be obvious when fresh presence has expired.
- Unavailable products and invalid cart items must be visible at item level.
- Order confirmation should clearly separate accepted order from editable cart state.

### Copy Requirements

- Customer copy should avoid security jargon such as token, idempotency, hash, credential, or session internals.
- Preferred concepts: "Scan the current QR", "This item is no longer available", "Review your cart", "Order received".
- Do not offer customer payment, cancellation, discount, refund, or close-session actions in v1.

## StationStaffApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, no station role |
| Station Selector | loading, no authorized stations, station disabled |
| Station Queue | loading, empty queue, grouped by status, stale item, unauthorized item removed |
| Item Detail Panel | loading, item not found, item stale, cannot_prepare reason required |
| Recent / Completed View | same-day recent items, no recent items |

### Empty States

- No authorized stations: show no station access, not an empty operational queue.
- Empty queue: show no active items for selected station.
- No recent items: show no recent station activity for current business day.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| User lacks station_staff role | Block app access |
| No station scope | Show no station access |
| Item outside authorized station | Remove from queue or reject action |
| Item already updated by another staff user | Refresh item and show current state |
| `cannot_prepare` reason missing | Block submit and focus reason input |
| Item already ready/delivered/closed | Reject stale transition |
| Station disabled | Remove active station operations |

### Success and Confirmation States

- Start preparing updates item state in place.
- Mark ready moves item out of active preparing state.
- Report cannot prepare marks item as exception and makes cashier attention visible.

### Stale and Retry States

- Duplicate transition clicks must not create duplicate transitions.
- Queue should refresh item state after stale transition rejection.
- If network fails after transition submit, retry must resolve to current server state.

### Visual Priority Rules

- Queue groups by preparation status.
- Items sort oldest first inside each group.
- Oldest pending item age must be visible.
- `cannot_prepare` requires a distinct attention state.

### Copy Requirements

- Do not use financial language for `cannot_prepare`.
- Use operational copy such as "Cannot prepare" and "Reason required".
- Do not expose payment or cashier-only notes.

## ServiceStaffApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, no service role |
| Service Tracking Disabled | blocked/no operational queue |
| Service Queue | loading, empty ready queue, grouped by table, stale item |
| Item Detail Panel | loading, item not found, unauthorized hall, already delivered |
| Bulk Delivery | selecting, invalid mixed-table selection, submitting, delivered |
| Recent Delivered View | same-day recent deliveries, no recent deliveries |

### Empty States

- Service tracking disabled: show no active service queue and route staff away from delivery controls.
- Empty ready queue: show no ready items for authorized halls.
- No recent deliveries: show no same-day delivered items.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| User lacks service_staff role | Block app access |
| No hall scope | Show no hall access |
| Service tracking disabled | Hide delivery mutation controls |
| Item not ready | Reject pickup/delivery |
| Item outside authorized hall | Reject and remove from queue |
| Item already delivered | Show delivered state; prevent mutation |
| Bulk selection spans multiple tables | Reject bulk action |
| Bulk selection contains stale item | Reject whole bulk action and refresh selection |

### Success and Confirmation States

- Picked up state updates item as in progress.
- Delivered state removes item from active queue and updates customer/cashier visibility.
- Bulk delivered state applies atomically to selected same-table items.

### Stale and Retry States

- Duplicate delivered command returns delivered state without duplicate mutation.
- Network retry uses same idempotency key for bulk delivery.
- Queue refreshes after service tracking setting changes.

### Visual Priority Rules

- Queue groups by table.
- Items sort oldest ready first inside each table group.
- Oldest ready item age must be visible.
- Picked-up items must be visually distinct from ready items.

### Copy Requirements

- Disabled mode copy should state that this tenant does not use separate delivery tracking.
- Do not imply `ready` is delivered when service tracking is enabled.

## CashierApp UI States

### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, OTP required, OTP expired |
| Cashier Workspace | loading, empty active sessions, grouped halls/tables, stale table state |
| Session Detail Panel | loading, no active session, active session, closed session, item exception attention |
| Payment Drawer/Dialog | empty amount, invalid amount, over-remaining amount, submitting, recorded |
| Correction Drawer/Dialog | note, item void, payment void, reason required, target invalid |
| Close Session Dialog | disabled until zero balance, confirming, closing, closed |
| Payment History | loading, empty today, payment voided, actor visible |

### Empty States

- No active sessions: show table board with available tables.
- Session panel for available table: show no active session.
- Payment History empty: show no current business-day payments.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| User lacks cashier role | Block app access |
| OTP required/expired | Continue first-login setup; do not open workspace |
| Payment amount zero/negative | Block submit |
| Payment exceeds remaining balance | Block/reject in v1 |
| Duplicate payment submit | Disable while pending; backend returns original payment |
| Check closed | Block payment/correction |
| Remaining balance above zero | Disable close session |
| Item void target not `pending` or `cannot_prepare` | Block/reject item void |
| Any payment exists on Check | Block/reject item void in v1 |
| Payment already voided | Show voided state |
| Reason missing for correction/void | Block submit and focus reason |
| Stale session state | Refresh panel and require user to retry action |

### Success and Confirmation States

- Payment success updates paid and remaining amounts server-side.
- Full payment enables explicit close action.
- Close success updates table to available.
- Item void success recalculates bill and marks item voided.
- Payment void success recalculates paid/remaining and shows reason.
- Correction note success appends audit-visible note.

### Stale and Retry States

- Multiple cashiers can operate same tenant; every action must handle stale totals.
- Payment and close actions must re-read server-calculated balance.
- Duplicate close returns already-closed result.
- Session detail should refresh after payment/correction/fulfillment changes.

### Visual Priority Rules

- Tables with active sessions must be distinguishable from available tables.
- Tables with `cannot_prepare` items need attention state.
- Remaining balance should be prominent.
- Closed sessions should not look actionable.

### Copy Requirements

- Use Check/Adisyon language for bill settlement.
- Do not expose customer payment, split check, item/person split, fiscal receipt, or external provider controls.
- Correction copy must make clear that every correction requires a reason and audit.

## UI State Coverage Checklist

Before detailed UI design is accepted, each app workspace must define:

- initial loading state;
- empty state;
- blocked/unauthorized state;
- validation error state;
- stale state;
- duplicate-submit pending state;
- success state;
- retry/recovery state;
- contextual panel/drawer/dialog behavior;
- copy that does not expose internals;
- backend invariant that enforces the UI state.
