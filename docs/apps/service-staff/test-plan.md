# ServiceStaffApp Test Plan

This document defines ServiceStaffApp-visible test coverage for v1. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

Source context:

- [definition.md](definition.md)
- [end-to-end.md](end-to-end.md)
- [scenarios.md](scenarios.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [wireframes.md](wireframes.md)
- [copy.md](copy.md)
- [components.md](components.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Test Scope

ServiceStaffApp tests prove that service staff can log in, see only authorized hall items when service tracking is enabled, pick up and deliver ready items, bulk deliver same-table items atomically, and inspect same-day recent deliveries without gaining setup, preparation, cashier, or payment authority.

Out of scope for this test plan:

- tenant setup changes;
- station preparation transitions;
- customer order creation;
- cashier payment/correction/session-close mutation;
- service-tracking setting mutation;
- fiscal, hardware, provider, or platform operations.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| SV-01 Login and Queue Entry | Staff logs in, changes bootstrap password if needed, tracking enabled opens authorized hall queue. |
| SV-02 Pick Up Item | Ready authorized item moves to picked_up and CustomerApp still shows preparing text. |
| SV-03 Mark Delivered | Ready or picked-up item moves to delivered and CustomerApp maps to delivered. |
| SV-04 Bulk Deliver Same Table Items | Same-table selected items are delivered atomically with one idempotency key. |

## Branch Coverage

### Login, Tracking, and Hall Access

| Branch | Expected Test Result |
| --- | --- |
| Service tracking disabled | No operational queue or delivery controls. |
| User lacks service_staff role | Block ServiceStaffApp. |
| No authorized halls | Show no hall access state. |
| Hall disabled after login | Remove/deny affected hall operations. |
| Invalid credentials | Reject safely. |
| Bootstrap password required | Password change required; no OTP. |

### Queue and Visibility

| Branch | Expected Test Result |
| --- | --- |
| Empty ready queue | Empty state for authorized halls. |
| Multiple table groups | Group by table and sort oldest ready first. |
| Picked-up item visible | Visually distinct picked-up state. |
| Unauthorized hall item | Remove or reject safely. |
| Already delivered item | Read-only delivered state. |
| Recent deliveries exist | Same-day recent view shows read-only activity. |
| No recent deliveries | Recent empty state. |

### Delivery Transitions

| Branch | Expected Test Result |
| --- | --- |
| Item not ready | Pickup/delivery rejected. |
| Ready item picked up | State becomes picked_up after backend acceptance. |
| Ready item delivered directly | Delivered allowed. |
| Picked-up item delivered | Delivered allowed. |
| Pending/preparing item delivered | Rejected. |
| Unauthorized hall | Rejected. |
| Duplicate delivered command | Delivered state returned or stale-rejected without duplicate mutation. |
| Service tracking disabled during action | Rejected and queue refreshed. |
| Closed TableSession | Rejected except explicit recovery. |

### Bulk Delivery

| Branch | Expected Test Result |
| --- | --- |
| Same-table ready/picked-up selection | Bulk delivered atomically. |
| Mixed-table selection | Bulk action blocked/rejected. |
| One selected item invalid | Whole command rejected; no partial delivery. |
| Duplicate bulk command | Original bulk result returned. |
| Same idempotency key different selection | Conflict returned. |
| Network retry | Same idempotency key prevents duplicate delivery. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Service staff login and bootstrap password change | Browser/API tests. |
| OTP not required for service staff | Login/first-password tests prove no OTP step. |
| Tracking checked before queue | Browser/API tracking-disabled tests. |
| Disabled tracking hides delivery controls | UI absence tests. |
| Authorized halls only | API/security and UI tests. |
| Queue groups by table and sorts oldest ready first | Component/E2E tests. |
| `ready -> delivered` works | API/domain/browser tests. |
| `ready -> picked_up -> delivered` works | API/domain/browser tests. |
| Bulk same-table only | Component/API tests. |
| Single transitions duplicate-safe, bulk idempotent, transitions audited | Integration/concurrency/idempotency tests. |
| CustomerApp shows delivered only after delivered when tracking enabled | Cross-app visibility tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, no service role |
| Service Tracking Disabled | blocked/no operational queue |
| Service Queue | loading, empty ready queue, grouped by table, stale item |
| Item Detail Panel | loading, item not found, unauthorized hall, already delivered |
| Bulk Delivery | selecting, invalid mixed-table selection, submitting, delivered |
| Recent Delivered View | same-day recent deliveries, no recent deliveries |

## API Usage Coverage

ServiceStaffApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/v1/auth/login-requirements` | First-password requirement discovery. |
| `POST /api/v1/auth/login` | ServiceStaff scope, missing role, invalid credentials. |
| `POST /api/v1/auth/first-password/begin` | Bootstrap password setup. |
| `POST /api/v1/auth/first-password/complete` | No OTP required for service staff. |
| `GET /api/v1/auth/session` | Protected route access. |
| `POST /api/v1/auth/logout` | Session revocation. |
| `GET /api/v1/service-staff/authorized-halls` | Hall scope and no-hall state. |
| `GET /api/v1/service-staff/ready-items` | Ready/picked-up queue, tracking disabled, hall scope. |
| `GET /api/v1/service-staff/recent-deliveries` | Same-day recent delivery visibility. |
| `GET /api/v1/service-staff/workload` | Counts and oldest age. |
| `POST /api/v1/service-staff/items/{orderItemId}/pick-up` | Valid, stale, unauthorized, tracking disabled. |
| `POST /api/v1/service-staff/items/{orderItemId}/deliver` | Direct ready delivery, picked-up delivery, duplicate-safe terminal behavior. |
| `POST /api/v1/service-staff/items/bulk-deliver` | Same-table, all-or-nothing, idempotency replay/conflict. |

## Security and Abuse Coverage

Required tests:

- tenant context is resolved from host/session, not body/query tenant IDs;
- staff cannot cross tenant hosts;
- staff without service_staff role cannot access ServiceStaffApp;
- hall scope is enforced server-side on every read and transition;
- frontend hall/table selection is not authorization proof;
- unsafe delivery requests require CSRF;
- service tracking disabled fails closed for every delivery mutation;
- single-item duplicate clicks/concurrent updates do not corrupt transitions;
- bulk delivery is all-or-nothing and idempotent;
- delivered/closed items are not mutable except explicit recovery;
- payment data, cashier-only notes, table-session settlement data, and preparation mutation controls are absent.

## Accessibility and Responsive Coverage

Required checks:

- login, queue filters, item panel, pickup/deliver actions, same-table selection, and bulk review work by keyboard;
- touch targets for pickup/deliver/bulk actions are large enough;
- status labels have accessible text;
- mixed-table bulk error is announced with text;
- queue updates do not steal focus;
- mobile drawer and desktop detail panel avoid overlapping table/product/station/note/action text.

## Copy Coverage

Tests must assert that:

- tracking disabled copy uses [copy.md](copy.md);
- `ready` is not presented as delivered while tracking is enabled;
- bulk delivery copy enforces same-table selection;
- stale/duplicate transition copy says current state is refreshed;
- payment, cashier correction, tenant setup, and station preparation labels are absent.

## Forbidden Control Coverage

ServiceStaffApp tests must prove these controls are absent:

- tenant setup/menu/staff editing;
- station preparation start/ready/cannot-prepare actions;
- customer order creation;
- payment receive/void/provider checkout;
- close table session;
- discount/refund/cancel item as financial correction;
- service-tracking setting toggle;
- cashier correction controls.

## Traceability

When implementation begins:

- browser E2E tests should reference ServiceStaffApp scenarios SV-01 through SV-04;
- API tests should reference [api-usage.md](api-usage.md) and Service Delivery/Staff Access contracts;
- bulk idempotency/race tests should reference Service Delivery transaction sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

ServiceStaffApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- service tracking disabled, hall scope, stale transition, duplicate-click, and bulk idempotency coverage are defined;
- no-OTP first-password behavior is defined;
- UI state and copy coverage are defined;
- forbidden ServiceStaffApp runtime/control leaks are explicitly tested absent;
- semantic index is regenerated after this document changes.
