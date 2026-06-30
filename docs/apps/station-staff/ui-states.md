# StationStaffApp UI States
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
