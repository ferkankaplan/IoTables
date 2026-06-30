# StationStaffApp Scenarios
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

- StationStaffApp + Preparation + Tenant Setup setting read.

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
