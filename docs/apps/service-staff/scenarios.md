# ServiceStaffApp Scenarios
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
