# API Contracts: Preparation

Source contracts: [preparation-contracts.md](preparation-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Preparation owns station queues and preparation status transitions.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/station-staff/queue` | StationStaffApp | `preparation.list_station_queue` | StationStaff session | Query: `stationId`, `status?`, `cursor`, `limit` | `PreparationQueue` | `outside_station_scope`, `missing_role` |
| `GET` | `/api/v1/station-staff/recent-items` | StationStaffApp | `preparation.list_station_recent_items` | StationStaff session | Query: `stationId`, `cursor`, `limit` | `StationRecentItemList` | `outside_station_scope`, `missing_role` |
| `GET` | `/api/v1/station-staff/workload` | StationStaffApp | `preparation.get_station_workload` | StationStaff session | Query: `stationId` | `StationWorkload` | `outside_station_scope` |
| `POST` | `/api/v1/station-staff/preparation-items/{preparationItemId}/start` | StationStaffApp | `preparation.start_preparing` | StationStaff session + CSRF | Path: `preparationItemId` | `PreparationItem` | `invalid_preparation_transition`, `outside_station_scope` |
| `POST` | `/api/v1/station-staff/preparation-items/{preparationItemId}/mark-ready` | StationStaffApp | `preparation.mark_ready` | StationStaff session + CSRF | Path: `preparationItemId` | `PreparationItem` | `invalid_preparation_transition`, `outside_station_scope` |
| `POST` | `/api/v1/station-staff/preparation-items/{preparationItemId}/cannot-prepare` | StationStaffApp | `preparation.report_cannot_prepare` | StationStaff session + CSRF | Body: `reason` | `PreparationItem` | `reason_required`, `invalid_preparation_transition`, `outside_station_scope` |
| `GET` | `/api/v1/cashier/order-items/{orderItemId}/preparation` | CashierApp | `preparation.read_preparation_state` | Cashier session | Path: `orderItemId` | `PreparationState` | `missing_role`, `not_found_or_hidden` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `preparation.create_queue_item` | Called by Customer Ordering inside order submission transaction. |
| `preparation.read_preparation_state` | Also consumed internally by Settlement and Service Delivery. CustomerApp normally receives this state through order list endpoints. |

## Request Schemas

`CannotPrepareRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `reason` | string | yes | Human-readable operational reason, safe for cashier visibility. |

## Response Schemas

`PreparationItem`:

| Field | Type | Notes |
| --- | --- | --- |
| `preparationItemId` | string | Queue item ID. |
| `orderItemId` | string | Linked order item. |
| `stationId` | string | Owning station. |
| `tableLabel` | string | Display label resolved from venue. |
| `itemLabel` | string | Order snapshot label. |
| `quantity` | integer | Ordered quantity. |
| `status` | string enum | `pending`, `preparing`, `ready`, `cannot_prepare`. |
| `orderedAt` | timestamp | UTC. |
| `startedAt` | timestamp/null | UTC. |
| `readyAt` | timestamp/null | UTC. |

`PreparationQueue` uses list envelope with `PreparationItem` items.

`StationRecentItemList` uses list envelope with same-day items that left the active station queue or reached a terminal/recent state visible to StationStaffApp.

`StationWorkload` includes station counters by status and oldest item age.

## Idempotency

Preparation transitions do not require `Idempotency-Key`. They are protected by row locks and explicit lifecycle transition guards. Repeating a completed transition returns `409 invalid_preparation_transition`.
