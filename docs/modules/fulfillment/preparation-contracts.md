# Module Contracts: Preparation

Source module: [preparation.md](preparation.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `preparation.create_queue_item` | Customer Ordering | tenantId, orderItemId, stationId | OrderItem/station same tenant; station enabled; one queue item per OrderItem | Insert PreparationItem in order transaction; unique orderItemId prevents duplicate queue item | Pending preparation item |
| `preparation.start_preparing` | StationStaffApp | preparationItemId | Actor has station assignment; status must be `pending` | Lock row; transition `pending -> preparing`; append transition | Updated preparation item |
| `preparation.mark_ready` | StationStaffApp | preparationItemId | Actor has station assignment; status must be `preparing` | Lock row; transition `preparing -> ready`; append transition | Ready preparation item |
| `preparation.report_cannot_prepare` | StationStaffApp | preparationItemId, reason | Actor has station assignment; status `pending` or `preparing`; reason required | Lock row; transition to `cannot_prepare`; append transition; audit/visibility event | Cannot-prepare item |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `preparation.list_station_queue` | StationStaffApp | actor, stationId/status filters | Station assignment required | Queue items for authorized station |
| `preparation.list_station_recent_items` | StationStaffApp | actor, stationId, current business day, cursor/limit | Station assignment required | Same-day recent/completed items for authorized station |
| `preparation.read_preparation_state` | CustomerApp, CashierApp, ServiceStaffApp | orderItemId or table session filter | Caller visibility enforced by app/module scope | Preparation status and timestamps |
| `preparation.get_station_workload` | StationStaffApp | actor, stationId | Station assignment required | Counts/age read model |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `staff_access.require_staff_permission` | Validate station staff and station scope. |
| `station_setup.get_station_context` | Validate station state/label. |
| `audit.record_event` | Record status changes when required. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `preparation.status_changed` | PreparationItem status changes | Customer/Cashier visibility, Service Delivery, Audit |
| `preparation.ready` | Item becomes ready | Service Delivery queue |
| `preparation.cannot_prepare` | Station reports exception | Cashier attention/correction flow |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `outside_station_scope` | Actor cannot operate this station. |
| `invalid_preparation_transition` | Current status does not allow requested transition. |
| `reason_required` | Cannot-prepare transition lacks reason. |
| `already_routed` | Queue item already exists for OrderItem. |
