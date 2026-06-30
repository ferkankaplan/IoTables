# ServiceStaffApp UI States
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
