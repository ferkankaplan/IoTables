# V1 State Visibility and Acceptance Criteria

This document defines what each app sees when shared operational state changes.

It prevents modules, schemas, and APIs from inventing different meanings for the same state.

Detailed happy paths and branch behavior are enumerated in [v1-scenario-catalog.md](v1-scenario-catalog.md). This document defines the visibility and acceptance checks those scenarios must satisfy.

## App Visibility Matrix

| State / Event | PlatformApp | TenantApp | CustomerApp | StationStaffApp | ServiceStaffApp | CashierApp |
| --- | --- | --- | --- | --- | --- | --- |
| Tenant `provisioning` | Full | Not available until tenant route resolves | Not available | Not available | Not available | Not available |
| Tenant `active` | Full | Own tenant access | Public/customer access allowed | Staff access allowed | Staff access allowed if enabled | Cashier access allowed |
| Tenant `suspended` | Full | Block tenant admin runtime access unless recovery policy says otherwise | Show unavailable | Block | Block | Block |
| Starter template applied | Full | Shows editable starter data | Indirect through menu/table availability | Indirect through station queues | Indirect through service users | Indirect through cashier user |
| Table display provisioned | Support/summary only | Full in table panel | Indirect through QR availability | None | None | Table state only |
| TableAccessToken redeemed | No normal view | No normal view | Creates/refreshes session and presence | None | None | No normal view |
| CustomerOrderingSession active | No | No | Own browser session | No | No | No |
| Cart active | No | No | Full for owning browser | No | No | No |
| Order submitted | Health/audit summary only if exposed | No direct mutation | Confirmation, My Orders, Table Orders | Assigned items appear | Later ready items appear | Session/order panel updates |
| Preparation `pending` | No | No | `Hazırlanıyor` | Visible if assigned station | Not yet visible | Visible in session item status |
| Preparation `preparing` | No | No | `Hazırlanıyor` | Visible if assigned station | Not yet visible | Visible in session item status |
| Preparation `ready` with service tracking enabled | No | No | `Hazırlanıyor` | Ready/recent state | Ready queue | Visible in session item status |
| Preparation `ready` with service tracking disabled | No | Tenant setting explains mode | `Teslim edildi` | Ready/final state | No queue | Visible as final tracked fulfillment |
| Preparation `cannot_prepare` | No | No direct runtime mutation | Still bill-visible unless cashier corrects | Visible exception | Not serviceable | Visible exception requiring cashier attention |
| Delivery `picked_up` | No | No | `Hazırlanıyor` | May leave active ready queue | Visible if authorized hall | Visible in session item status |
| Delivery `delivered` | No | No | `Teslim edildi` | Recent/history only | Delivered/recent state | Visible in session item status |
| Payment recorded | No direct runtime mutation | No | Read-only bill/balance update after fresh presence | No | No | Full |
| Payment voided | No direct runtime mutation | No | Read-only bill/balance update after fresh presence | No | No | Full with reason |
| Cashier correction note | No normal view | Audit if exposed | No | No | No | Full |
| Item void by cashier | No normal view | Audit if exposed | Table bill/order state updates read-only | Removed/marked outside active prep if still pending/cannot_prepare | Not serviceable | Full with reason |
| TableSession closed | Health/summary only if exposed | No runtime mutation | Requires fresh QR for any new order context | Closed items no longer mutable | Closed items no longer mutable | Full |

## CustomerApp Acceptance Criteria

CustomerApp is accepted for v1 when:

- a customer can scan a fresh QR and reach the menu;
- expired, reused, or wrong-table QR tokens fail without exposing internals;
- cart survives fresh QR re-verification while the CustomerOrderingSession remains recoverable;
- order submit requires fresh table presence;
- duplicate submit does not create duplicate orders;
- failed submit keeps cart editable;
- successful submit clears only the submitted cart;
- My Orders shows multiple orders from the same CustomerOrderingSession;
- Table Orders requires fresh presence and shows all active TableSession orders;
- read-only bill/balance requires fresh presence and is server-calculated;
- customers cannot pay, close, cancel, discount, refund, or edit submitted orders;
- visible statuses match service delivery tracking mode.

## PlatformApp Acceptance Criteria

PlatformApp is accepted for v1 when:

- Platform Owner must log in before seeing tenants;
- first Platform Owner bootstrap is explicit and one-time;
- Platform Owner must complete password change and TOTP enrollment;
- tenant creation requires name, subdomain, and GSM number;
- tenant starts as `provisioning`;
- tenant becomes `active` only after required setup records commit;
- provisioning failure is visible and recoverable;
- starter template is applied exactly once;
- manual DNS readiness is trackable but not automated;
- PlatformApp cannot mutate tenant runtime orders, payments, sessions, preparation, or delivery as a normal flow.

## TenantApp Acceptance Criteria

TenantApp is accepted for v1 when:

- public tenant page exposes only safe public tenant fields;
- tenant admin login requires first password change and OTP through tenant GSM;
- tenant name and subdomain are not editable;
- halls and tables are managed in one workspace with contextual table panels;
- v1 table layout is an ordered grid, not floor-plan coordinates;
- table display provisioning is available from table detail;
- stations can be created/disabled;
- menu categories, products/services, modifiers, prices, availability, and one station assignment can be managed;
- each product/service has exactly one station in v1;
- service delivery tracking can be explicitly enabled/disabled;
- staff roles, station scopes, and service hall scopes can be managed;
- configuration changes that affect access, ordering, fulfillment, or customer-visible identity are audited.

## StationStaffApp Acceptance Criteria

StationStaffApp is accepted for v1 when:

- station staff must log in and change bootstrap password on first login;
- OTP is not required for station staff in v1;
- one authorized station opens directly;
- multiple authorized stations require station selection;
- unauthorized stations are not visible or mutable;
- queue groups by preparation status and sorts oldest first;
- staff can move `pending -> preparing -> ready`;
- staff can move `pending/preparing -> cannot_prepare` with reason;
- duplicate or concurrent state changes are safe;
- customer preparation notes are visible when relevant;
- cashier-only notes and payment data are not visible.

## ServiceStaffApp Acceptance Criteria

ServiceStaffApp is accepted for v1 when:

- service staff must log in and change bootstrap password on first login;
- OTP is not required for service staff in v1;
- service delivery tracking is checked before showing the queue;
- disabled service tracking hides delivery controls;
- service staff sees only authorized halls;
- queue groups by table and sorts oldest ready item first;
- staff can mark `ready -> delivered`;
- staff may mark `ready -> picked_up -> delivered`;
- bulk delivery is allowed only for selected same-table items;
- delivery transitions are idempotent and audited;
- CustomerApp shows `Teslim edildi` only after delivered when service tracking is enabled.

## CashierApp Acceptance Criteria

CashierApp is accepted for v1 when:

- cashier must log in and change bootstrap password on first login;
- cashier first password setup requires OTP through tenant GSM;
- cashier sees halls, tables, active sessions, latest order state, total, paid, and remaining balance;
- session detail opens in context without losing table board;
- every active TableSession has exactly one Check/Adisyon;
- payments are recorded against the Check;
- partial payments reduce remaining balance but do not close the session;
- zero balance enables explicit closure but does not silently close;
- duplicate payment submit does not create duplicate payment records;
- duplicate close request is idempotent;
- only v1 allowed corrections are available;
- all payments, voids, corrections, and closures are audited;
- CustomerApp payment, split check, item/person split, fiscal receipt, and external provider flows are absent.

## Cross-App Invariants

- Tenant context is resolved server-side.
- Frontend-provided table IDs, station IDs, session IDs, permissions, prices, and totals are never authoritative.
- One active TableSession may exist per tenant/table.
- One Check/Adisyon exists per TableSession in v1.
- CustomerOrderingSession and TableSession remain separate.
- Cart is not billable.
- OrderItem price snapshots are server-created and immutable except allowed void metadata.
- Service delivery tracking mode changes customer-visible status semantics.
- Critical commands are idempotent.
- State mutations that affect orders, checks, payments, preparation, delivery, sessions, or provisioning are transactional where possible and audited where required.

## UI Detailing Follow-Ups

These are not schema/API blockers. They should be resolved during detailed UI design without changing the v1 app semantics above:

- exact customer-facing copy for QR/session/order errors;
- empty/loading/error states per app workspace;
- same-day recent history limits for station and service queues;
- visual priority thresholds for old orders/items.

Tenant-level restaurant open/closed scheduling is out of v1. TenantApp may expose static public tenant information, but v1 orderability is controlled by tenant status, table state, product/service availability, station availability, and fresh QR presence.
