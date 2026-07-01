# StationStaffApp Test Plan

This document defines StationStaffApp-visible test coverage for v1. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

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

StationStaffApp tests prove that station staff can log in, select authorized stations, view assigned queue items, move items through valid preparation states, report `cannot_prepare` with reason, and inspect same-day recent work without gaining tenant setup, cashier, payment, or service delivery authority.

Out of scope for this test plan:

- tenant setup changes;
- product/station/menu reassignment;
- customer order creation;
- cashier payment/correction/session-close mutation;
- service delivery pickup/delivered mutation;
- fiscal, hardware, provider, or platform operations.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| S-01 Login and Queue Entry | Staff logs in, changes bootstrap password if needed, direct queue for one station, selector for multiple stations. |
| S-02 Start Preparing Item | `pending -> preparing` with station authorization and actor transition record. |
| S-03 Mark Item Ready | `preparing -> ready`; visibility follows service tracking mode. |
| S-04 Report Cannot Prepare | `pending/preparing -> cannot_prepare` with required reason and cashier-visible exception. |

## Branch Coverage

### Login and Station Access

| Branch | Expected Test Result |
| --- | --- |
| Invalid credentials | Reject safely. |
| User disabled | Reject access. |
| User lacks station_staff role | Block StationStaffApp. |
| No authorized stations | Show no station access state. |
| One authorized station | Open queue directly. |
| Multiple authorized stations | Show station selector. |
| Station disabled after login | Remove from selector/queue or reject next action. |

### Queue and Item Visibility

| Branch | Expected Test Result |
| --- | --- |
| Empty active queue | Empty queue state for selected station. |
| Queue has multiple statuses | Group by status and sort oldest first. |
| Unauthorized item appears due stale client state | Remove item or reject action safely. |
| Customer prep note exists | Visible when preparation-relevant. |
| Cashier-only note/payment data exists | Not visible. |
| Recent items exist | Same-day recent view shows read-only activity. |
| No recent items | Recent empty state. |

### Preparation Transitions

| Branch | Expected Test Result |
| --- | --- |
| Item outside authorized station | Reject. |
| Pending item started | Status becomes preparing after backend acceptance. |
| Already preparing item start attempted | Current state returned or stale rejection without duplicate transition. |
| Pending item marked ready directly | Reject unless future shortcut is explicitly introduced. |
| Preparing item marked ready | Status becomes ready after backend acceptance. |
| Already ready item marked ready | Current state returned or stale rejection without duplicate transition. |
| Cannot prepare without reason | Reject and focus reason field. |
| Cannot prepare after ready/picked_up/delivered | Reject. |
| TableSession closed | Reject except explicit recovery. |
| Duplicate click/network retry | No duplicate transition corruption; UI refreshes current server state. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Station staff login and bootstrap password change | Browser/API tests. |
| OTP not required for station staff | Login/first-password tests prove no OTP step. |
| One station opens directly | Browser routing test. |
| Multiple stations require selector | Browser routing test. |
| Unauthorized stations not visible/mutable | API/security and UI tests. |
| Queue groups by status and sorts oldest first | Component/E2E tests. |
| `pending -> preparing -> ready` works | API/domain/browser tests. |
| `pending/preparing -> cannot_prepare` requires reason | API/component/browser tests. |
| Duplicate/concurrent state changes are safe | Integration/concurrency tests. |
| Customer prep notes visible when relevant | Visibility tests. |
| Cashier-only notes/payment data absent | Negative UI/API tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| Login | loading, invalid credentials, first password change required, no station role |
| Station Selector | loading, no authorized stations, station disabled |
| Station Queue | loading, empty queue, grouped by status, stale item, unauthorized item removed |
| Item Detail Panel | loading, item not found, item stale, cannot_prepare reason required |
| Recent / Completed View | same-day recent items, no recent items |

## API Usage Coverage

StationStaffApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/v1/auth/login-requirements` | First-password requirement discovery. |
| `POST /api/v1/auth/login` | StationStaff scope, missing role, invalid credentials. |
| `POST /api/v1/auth/first-password/begin` | Bootstrap password setup. |
| `POST /api/v1/auth/first-password/complete` | No OTP required for station staff. |
| `GET /api/v1/auth/session` | Protected route access. |
| `POST /api/v1/auth/logout` | Session revocation. |
| `GET /api/v1/station-staff/authorized-stations` | Station selector/direct queue behavior. |
| `GET /api/v1/station-staff/stations/{stationId}/context` | Disabled/out-of-scope station handling. |
| `GET /api/v1/station-staff/queue` | Assigned station queue, grouping/filtering inputs. |
| `GET /api/v1/station-staff/recent-items` | Same-day recent items. |
| `GET /api/v1/station-staff/workload` | Counts and oldest age. |
| `POST /api/v1/station-staff/preparation-items/{preparationItemId}/start` | Valid, stale, unauthorized, duplicate-safe start. |
| `POST /api/v1/station-staff/preparation-items/{preparationItemId}/mark-ready` | Valid, stale, unauthorized, duplicate-safe ready. |
| `POST /api/v1/station-staff/preparation-items/{preparationItemId}/cannot-prepare` | Reason required, stale, unauthorized, invalid states. |

## Security and Abuse Coverage

Required tests:

- tenant context is resolved from host/session, not body/query tenant IDs;
- staff cannot cross tenant hosts;
- staff without station_staff role cannot access StationStaffApp;
- station scope is enforced server-side on every queue read and transition;
- frontend station selection is not authorization proof;
- unsafe transition requests require CSRF;
- duplicate clicks/concurrent updates do not corrupt transitions;
- closed/completed items are not mutable;
- `cannot_prepare` cannot cancel, discount, refund, reprice, close session, or remove billable records;
- cashier-only notes, payment data, and table-session settlement data are absent.

## Accessibility and Responsive Coverage

Required checks:

- login, station selector, queue filters, item panel, action bar, and cannot-prepare dialog work by keyboard;
- touch targets for start/ready/cannot-prepare actions are large enough;
- status labels have accessible text;
- cannot-prepare missing reason focuses the reason field;
- queue updates do not steal focus;
- mobile drawer and desktop detail panel avoid overlapping table/product/note/action text.

## Copy Coverage

Tests must assert that:

- station action labels use [copy.md](copy.md);
- `cannot_prepare` copy does not use financial language;
- stale/duplicate transition copy says current state is being refreshed;
- unauthorized station copy is safe;
- payment, cashier correction, tenant setup, and delivery labels are absent.

## Forbidden Control Coverage

StationStaffApp tests must prove these controls are absent:

- tenant setup/menu/staff editing;
- customer order creation;
- payment receive/void/provider checkout;
- close table session;
- discount/refund/cancel item as financial correction;
- service delivery pickup/delivered controls;
- station reassignment controls;
- cashier correction controls.

## Traceability

When implementation begins:

- browser E2E tests should reference StationStaffApp scenarios S-01 through S-04;
- API tests should reference [api-usage.md](api-usage.md) and Preparation/Staff Access contracts;
- transition race tests should reference Preparation transaction/lock sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

StationStaffApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- station scope, stale transition, duplicate-click, and concurrency coverage are defined;
- no-OTP first-password behavior is defined;
- UI state and copy coverage are defined;
- forbidden StationStaffApp runtime/control leaks are explicitly tested absent;
- semantic index is regenerated after this document changes.
