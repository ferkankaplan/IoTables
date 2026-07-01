# API Contracts: Service Delivery

Source contracts: [service-delivery-contracts.md](service-delivery-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Service Delivery owns picked-up and delivered states after preparation readiness. Readiness itself comes from PreparationItem.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/service-staff/ready-items` | ServiceStaffApp | `service_delivery.list_ready_items` | ServiceStaff session | Query: `hallId?`, `status?`, `cursor`, `limit` | `ServiceReadyItemList` | `service_tracking_disabled`, `outside_hall_scope` |
| `GET` | `/api/v1/service-staff/recent-deliveries` | ServiceStaffApp | `service_delivery.list_recent_deliveries` | ServiceStaff session | Query: `hallId?`, `cursor`, `limit` | `ServiceRecentDeliveryList` | `service_tracking_disabled`, `outside_hall_scope` |
| `GET` | `/api/v1/service-staff/workload` | ServiceStaffApp | `service_delivery.get_service_workload` | ServiceStaff session | Query: `hallId?` | `ServiceWorkload` | `service_tracking_disabled`, `outside_hall_scope` |
| `POST` | `/api/v1/service-staff/items/{orderItemId}/pick-up` | ServiceStaffApp | `service_delivery.mark_picked_up` | ServiceStaff session + CSRF | Path: `orderItemId` | `DeliveryState` | `not_ready_for_delivery`, `outside_hall_scope`, `invalid_delivery_transition` |
| `POST` | `/api/v1/service-staff/items/{orderItemId}/deliver` | ServiceStaffApp | `service_delivery.mark_delivered` | ServiceStaff session + CSRF | Path: `orderItemId` | `DeliveryState` | `not_ready_for_delivery`, `outside_hall_scope`, `invalid_delivery_transition` |
| `POST` | `/api/v1/service-staff/items/bulk-deliver` | ServiceStaffApp | `service_delivery.bulk_mark_delivered` | ServiceStaff session + CSRF + `Idempotency-Key` | Body: `BulkDeliverRequest` | `BulkDeliveryResult` | `bulk_mixed_table`, `bulk_item_invalid`, `idempotency_conflict`, `service_tracking_disabled` |
| `GET` | `/api/v1/cashier/order-items/{orderItemId}/delivery` | CashierApp | `service_delivery.read_delivery_state` | Cashier session | Path: `orderItemId` | `DeliveryReadState` | `missing_role`, `not_found_or_hidden` |

## Response Schemas

`ServiceReadyItem`:

| Field | Type | Notes |
| --- | --- | --- |
| `orderItemId` | string | Order item. |
| `preparationItemId` | string | Preparation item. |
| `tableId` | string | Table. |
| `hallId` | string | Hall used for scope. |
| `tableLabel` | string | Display label. |
| `itemLabel` | string | Order snapshot label. |
| `quantity` | integer | Ordered quantity. |
| `preparationReadyAt` | timestamp | Comes from PreparationItem. |
| `deliveryStatus` | string enum/null | `picked_up`, `delivered`, or null when not yet tracked. |

`DeliveryState` includes `orderItemId`, `preparationItemId`, `status`, `pickedUpAt?`, `deliveredAt?`, and `actorDisplayName?`.

`ServiceRecentDeliveryList` uses list envelope with same-day delivered/recent items visible to ServiceStaffApp for authorized halls.

`BulkDeliverRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `tableId` | string | yes | All selected items must belong to this table. |
| `orderItemIds` | string array | yes | Every item must be ready or picked up and in actor's hall scope. |

The API layer computes the normalized request hash from actor, table, route, and ordered item IDs. The client sends only `Idempotency-Key`, not a request hash.

`BulkDeliveryResult` includes `tableId`, `deliveredItems`, `alreadyDeliveredItems` when returned from compatible replay, `deliveredAt`, `actorDisplayName`, and `duplicate`.

`DeliveryReadState` maps customer/cashier visibility. When service tracking is disabled, it returns derived readiness from Preparation without creating DeliveryState.

## Transition Rules

- `ready -> picked_up -> delivered` is allowed.
- Direct `ready -> delivered` is allowed.
- Delivered items cannot move backward in v1.

## Idempotency

Single-item delivery transitions do not require `Idempotency-Key`. They are protected by row locks and lifecycle guards. A repeated terminal transition returns current state only if the same terminal result is already committed; otherwise it returns `409 invalid_delivery_transition`.

Bulk delivery requires `Idempotency-Key`. Same key and same request returns the original `BulkDeliveryResult`; same key with different table/items returns `409 idempotency_conflict`.
