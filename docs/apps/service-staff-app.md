# ServiceStaffApp

## Purpose

ServiceStaffApp is the tenant-scoped service delivery console for staff who deliver prepared items from stations to tables.

It is served from the tenant subdomain:

```text
https://[tenant].iotables.net
```

ServiceStaffApp closes the operational gap between station preparation and customer delivery. StationStaffApp marks items as ready; ServiceStaffApp picks up ready items and marks them delivered to the customer.

ServiceStaffApp is not a tenant setup interface, customer ordering interface, station preparation console, or cashier console. It does not manage products, prices, payments, table settlement, or station preparation state.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Waiter | Own tenant, assigned halls | View ready items for authorized halls and mark items delivered | Cannot receive payments or edit tenant setup |
| Busser | Own tenant, assigned halls/service support scope | View and support delivery/clearing tasks for authorized halls where permitted | Cannot receive payments or edit tenant setup |
| Service Staff | Own tenant, assigned halls/service scope | Operate allowed delivery workflows | Cannot prepare station items unless separately authorized |

Starter service staff users may be created automatically by a sector starter template. For the initial `cafe` template:

| Staff User | Username | Temporary Password | Initial Scope |
| --- | --- | --- | --- |
| Garson | `garson` | `admin` | Service delivery |
| Komi | `komi` | `admin` | Service support |

Starter service staff must change the temporary password on first login. OTP is not required for service staff in the first version because these roles do not perform critical financial or administrative operations. After creation, they are normal tenant-owned staff users.

## App Authority

ServiceStaffApp can operate delivery state for order items that are ready for service.

| Area | Authority |
| --- | --- |
| Ready queue | Read items marked ready by stations |
| Pickup state | Optionally mark ready items as picked up for delivery |
| Delivery state | Mark PreparationItem.ready or picked-up items as delivered to the table |
| Table context | Read hall/table context needed for delivery |
| Delivery workload | View ready and picked-up item counts |

ServiceStaffApp must always be tenant-scoped and hall-scoped. Staff can only see and operate delivery items for halls they are authorized for.

## Not Authorized

- It does not create or suspend tenants.
- It does not edit tenant identity or tenant setup data.
- It does not create halls, tables, stations, products, prices, or menu categories.
- It does not create customer orders.
- It does not prepare station items.
- It does not receive payments or close table sessions.
- It does not change item price snapshots.
- It does not rewrite station preparation state except through an explicit correction workflow.

## UX Principle

ServiceStaffApp should be a fast operational board focused on moving ready items to tables.

Staff should see ready items immediately, grouped in a way that makes physical service easy. Item details should open in a contextual panel or drawer without leaving the queue.

Large touch targets, clear table identifiers, station labels, and stable ready-item grouping matter more than configuration density.

## Screens and URLs

| Screen | URL | Purpose |
| --- | --- | --- |
| Service Login | `https://[tenant].iotables.net/service/login` | Authenticate service staff |
| Service Queue | `https://[tenant].iotables.net/service` | Show ready and picked-up items |
| Item Detail Panel | `https://[tenant].iotables.net/service?item=:orderItemId` | Deep-link to an item while staying in the service queue |

The service queue is the primary workspace. Item details should not be separate primary pages in the first version.

## Core Workflows

### Service Staff Login

1. Staff opens `https://[tenant].iotables.net/service/login`.
2. ServiceStaffApp authenticates against the current tenant.
3. If the staff user is using a temporary bootstrap password, ServiceStaffApp forces password change.
4. ServiceStaffApp opens the service queue.

### Monitor Ready Items

1. Staff opens the service queue.
2. ServiceStaffApp shows items marked `ready` by stations for the staff member's authorized halls.
3. Items show table, station, product/service name, quantity, notes, and age.
4. Staff can group or filter items by table, station, and age.

### Pick Up Item

1. Staff selects a ready item.
2. Staff optionally marks the item as `picked_up`.
3. ServiceStaffApp records who picked it up and when.
4. Other operational views can reflect that the item is on the way.

### Mark Delivered

1. Staff selects a ready or picked-up item.
2. Staff marks it as `delivered`.
3. ServiceStaffApp records who delivered it and when.
4. CustomerApp can show the item as `Teslim edildi`.

## Delivery States

Initial delivery state model:

```text
PreparationItem.ready -> delivered
PreparationItem.ready -> picked_up -> delivered
```

`ready` is created by StationStaffApp as PreparationItem state. DeliveryState stores only ServiceStaffApp-owned `picked_up` and `delivered` states.

State transitions must be controlled. An item must not jump backward or skip required states unless an explicit correction workflow exists.

## Data Concepts Visible in ServiceStaffApp

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Summary | Tenant identity resolved from subdomain |
| Station | Summary | Where the ready item came from |
| Order item | Full delivery view | Unit of service delivery work |
| Order | Summary | Used for grouping and context |
| Hall | Summary | Helps staff locate table |
| Table | Summary | Delivery destination |
| Product/service | Summary | Name, quantity, and delivery-relevant metadata |
| Delivery status | Full | Service-owned status after station readiness |
| Item note | Read | Customer or operational note if available |

## Operational Safety

ServiceStaffApp updates live delivery state, so transitions must be safe under duplicate clicks, retries, and concurrent staff actions.

- Delivery transitions must be idempotent.
- Delivery transitions must validate the current state server-side.
- A staff user must not view or update items outside authorized halls/service scope.
- Two staff users updating the same item concurrently must not corrupt state.
- Every delivery transition should record who changed it and when.
- Delivered or closed-session items must not be modified except through explicit recovery workflows.
- ServiceStaffApp must not trust frontend-visible table or item IDs as authorization proof.

## Integration Expectations

| Future Module | Expected Use |
| --- | --- |
| Identity and Access | Service staff authentication and service permission enforcement |
| Venue Layout | Read hall and table context |
| Ordering | Read order items |
| Preparation | Consume station-ready items |
| Service Delivery | Manage pickup and delivery status transitions |
| CustomerApp | Expose delivered status to customer views |
| Cashier / Session View | Expose delivery status to cashier context |
| Audit | Record service delivery transitions |

## Security Rules

- ServiceStaffApp resolves tenant context from `[tenant].iotables.net`.
- Service staff can access only their own tenant.
- Service routes require authentication.
- Service actions require service-staff permission.
- Service staff can only view and update ready/delivery items for authorized halls.
- Starter service staff passwords are temporary and must be changed on first login.
- Service staff first-login password change does not require OTP.
- ServiceStaffApp must not expose TenantApp configuration, StationStaffApp preparation controls, or CashierApp payment capabilities.

## Open Questions

- Should ready items be grouped by table, station, age, or order?
- Can service staff mark multiple items delivered in bulk?
- Which service metrics are needed in the first version?
