# ServiceStaffApp End-to-End Role

This document extracts the parts of the shared current release end-to-end flow where this app participates.

See the full shared flow: [../_shared/canonical-end-to-end.md](../_shared/canonical-end-to-end.md).

### 7. Service Staff Delivers Items
When service delivery tracking is enabled:

1. Service staff logs into ServiceStaffApp.
2. Staff sees ready items for authorized halls.
3. Items are grouped by table and sorted by oldest ready item inside each table group.
4. Staff may mark an item `picked_up`.
5. Staff marks item `delivered`.
6. CustomerApp maps delivered items to `Teslim edildi`.

When service delivery tracking is disabled:

1. ServiceStaffApp exposes no operational queue.
2. DeliveryState does not run.
3. `PreparationItem.ready` is the final tracked fulfillment state.
4. CustomerApp maps `ready` to `Teslim edildi`.

Acceptance criteria:

- Service staff cannot operate unauthorized halls.
- Delivery commands fail closed when service delivery tracking is disabled.
- Bulk delivery is allowed only for selected items on the same table.
- Bulk delivery is idempotent and validates every selected item server-side.
