# StationStaffApp

## Purpose

StationStaffApp is the tenant-scoped preparation console for staff working at fulfillment stations such as kitchen and coffee.

It is served from the tenant subdomain:

```text
https://[tenant].iotables.net
```

StationStaffApp shows the order items assigned to the staff member's station and lets staff move those items through preparation states.

StationStaffApp is not a tenant setup interface, customer ordering interface, cashier console, or service delivery app. It does not manage halls, tables, products, prices, payments, table session settlement, or customer delivery confirmation.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Cook | Own tenant, assigned kitchen station | View and update kitchen items | Cannot see unrelated station queues unless permitted |
| Barista | Own tenant, assigned coffee station | View and update coffee items | Cannot see unrelated station queues unless permitted |
| Station Staff | Own tenant, assigned stations | View and update allowed station items | Cannot configure stations or products |

Starter station staff users may be created automatically by a sector starter template. For the initial `cafe` template:

| Staff User | Username | Temporary Password | Initial Station |
| --- | --- | --- | --- |
| Aşçı | `asci` | `admin` | `Mutfak` |
| Barista | `barista` | `admin` | `Kahve` |

Starter station staff must change the temporary password on first login. OTP is not required for station staff because these roles do not perform critical financial or administrative operations. After creation, they are normal tenant-owned staff users.

## App Authority

StationStaffApp can operate preparation state for order items assigned to authorized stations.

| Area | Authority |
| --- | --- |
| Station queue | Read order items assigned to authorized stations |
| Preparation status | Move assigned items through allowed preparation states |
| Item readiness | Mark assigned items as ready |
| Item notes | Read customer or cashier-visible preparation notes when available |
| Station workload | View active item counts and age of waiting items |

StationStaffApp must always be tenant-scoped and station-scoped. A staff user can only see and update stations they are authorized for.

## Not Authorized

- It does not create or suspend tenants.
- It does not edit tenant identity or tenant setup data.
- It does not create halls, tables, stations, products, prices, or menu categories.
- It does not create customer orders.
- It does not receive payments or close table sessions.
- It does not change item price snapshots.
- It does not mark items as delivered to the customer.
- It does not reassign products to stations unless an explicit tenant admin workflow exists.

## UX Principle

StationStaffApp should be a fast, low-friction operational board.

Staff should see their active queue immediately after login. The interface should minimize navigation and optimize for repeated actions: start preparation, mark ready, and inspect item details. Item detail should open in a contextual panel or drawer without leaving the queue.

Large touch targets, clear status colors, and stable item positions matter more than dense configuration controls.

## Screens and URLs

| Screen | URL | Purpose |
| --- | --- | --- |
| Station Login | `https://[tenant].iotables.net/station/login` | Authenticate station staff |
| Station Queue | `https://[tenant].iotables.net/station` | Show assigned station items |
| Station Selector | `https://[tenant].iotables.net/station/select` | Choose among authorized stations when staff has more than one |
| Item Detail Panel | `https://[tenant].iotables.net/station?item=:orderItemId` | Deep-link to an item while staying in the station queue |

The station queue is the primary workspace. Item details should not be separate primary pages in the first version.

## Core Workflows

### Station Staff Login

1. Staff opens `https://[tenant].iotables.net/station/login`.
2. StationStaffApp authenticates against the current tenant.
3. If the staff user is using a temporary bootstrap password, StationStaffApp forces password change.
4. If the staff user has one authorized station, StationStaffApp opens that station queue.
5. If the staff user has multiple authorized stations, StationStaffApp opens station selection.

### Monitor Station Queue

1. Staff opens the station queue.
2. StationStaffApp shows active order items assigned to the selected station.
3. Items show table, order time, product/service name, quantity, notes, and current status.
4. Staff can filter or group items by status when needed.

StationStaffApp works on order items, not whole orders. One customer order may create work for multiple stations.

### Start Preparing Item

1. Staff selects an item in `pending` state.
2. Staff marks the item as `preparing`.
3. StationStaffApp records the status transition.
4. Other station views and cashier views can reflect the updated state.

### Mark Item Ready

1. Staff selects an item in `preparing` state.
2. Staff marks the item as `ready`.
3. StationStaffApp records the status transition.
4. The item becomes visible as ready to the appropriate operational views.

## Preparation States

Initial state model:

```text
pending -> preparing -> ready
```

`ready` means station work is finished and the item is ready for service staff. It does not mean the item was delivered to the customer.

State transitions must be controlled. An item must not jump backward or skip required states unless an explicit correction workflow exists.

## Data Concepts Visible in StationStaffApp

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Summary | Tenant identity resolved from subdomain |
| Station | Full for authorized stations | Staff queue context |
| Order item | Full operational view | Unit of station work |
| Order | Summary | Used for grouping and context |
| Table | Summary | Shows where the item belongs |
| Product/service | Summary | Name, quantity, and preparation-relevant metadata |
| Preparation status | Full | Station-owned status for assigned item |
| Item note | Read | Customer or operational note if available |

## Operational Safety

StationStaffApp updates live order item state, so transitions must be safe under duplicate clicks, retries, and concurrent staff actions.

- Status transitions must be idempotent.
- Status transitions must validate the current state server-side.
- A staff user must not update items outside authorized stations.
- Two staff users updating the same item concurrently must not corrupt state.
- Every status transition should record who changed it and when.
- Completed or closed-session items must not be modified except through explicit recovery workflows.
- StationStaffApp must not trust frontend-visible station IDs as authorization proof.

## Integration Expectations

| Future Context / Module | Expected Use |
| --- | --- |
| Identity and Access | Station staff authentication and station permission enforcement |
| Venue Layout | Read table context |
| Menu Catalog | Read product/service station assignment |
| Ordering | Read order items assigned to stations |
| Preparation | Manage preparation queues and status transitions |
| Service Delivery | Consume ready items and mark delivery state |
| Cashier / Session View | Expose preparation status to cashier context |
| Audit | Record station status transitions |

## Security Rules

- StationStaffApp resolves tenant context from `[tenant].iotables.net`.
- Station staff can access only their own tenant.
- Station routes require authentication.
- Station actions require station-staff permission.
- Staff can only view and update authorized stations.
- Starter station staff passwords are temporary and must be changed on first login.
- Station staff first-login password change does not require OTP.
- StationStaffApp must not expose TenantApp configuration or CashierApp payment capabilities.

## Open Questions

- Can one staff user operate multiple stations at the same time?
- Should station items be grouped by order, by product, by table, or by age?
- Can station staff reject or report an item they cannot prepare?
- Can station staff see customer notes?
- Should ready items remain visible after handoff to service staff?
- Which station metrics are needed in the first version?
