# API Contracts: Station Setup

Source contracts: [station-setup-contracts.md](station-setup-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Station Setup owns station definitions and lifecycle. It does not own preparation queue items.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/tenant-setup/stations` | TenantApp | `station_setup.list_stations` | Tenant Admin session | Query: `includeDisabled?` | `StationList` | `not_authorized` |
| `POST` | `/api/v1/tenant-setup/stations` | TenantApp | `station_setup.create_station` | Tenant Admin session + CSRF | Body: `StationWriteRequest` | `Station` | `duplicate_station`, `validation_failed` |
| `PATCH` | `/api/v1/tenant-setup/stations/{stationId}` | TenantApp | `station_setup.update_station` | Tenant Admin session + CSRF | Body: editable station fields | `Station` | `duplicate_station`, `not_found_or_hidden` |
| `POST` | `/api/v1/tenant-setup/stations/{stationId}/disable` | TenantApp | `station_setup.disable_station` | Tenant Admin session + CSRF | Body: `reason` | `Station` | `station_has_orderable_products`, `station_has_active_queue`, `reason_required` |
| `GET` | `/api/v1/station-staff/stations/{stationId}/context` | StationStaffApp | `station_setup.get_station_context` | StationStaff session | Path: `stationId` | `StationContext` | `outside_station_scope`, `station_unavailable` |

## Request Schemas

`StationWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Unique in tenant. |
| `displayOrder` | integer | yes | Unique in tenant. |

## Response Schemas

`Station` includes `stationId`, `name`, `displayOrder`, `enabled`, `createdAt`, and `updatedAt`.

`StationContext` includes `stationId`, `name`, `enabled`, and safe queue display metadata. It must not expose other station queues.

## Idempotency

Station create/update/disable endpoints do not require `Idempotency-Key`. Name/order uniqueness and station lifecycle guards protect duplicates and unsafe disablement.
