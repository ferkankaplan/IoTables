# API Contracts: Venue Layout

Source contracts: [venue-layout-contracts.md](venue-layout-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Venue Layout owns halls, 100-slot table ranges, table modes, ordered display, and table context. It does not own orders, sessions, payments, or fulfillment state.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/tenant-setup/venue/board` | TenantApp | `venue_layout.get_hall_table_board` | Tenant Admin session | none | `HallTableBoard` | `not_authorized` |
| `GET` | `/api/cashier/venue/board` | CashierApp | `venue_layout.get_hall_table_board` | Cashier session | Query: `includeVirtualTestTables?` | `CashierHallTableBoard` | `missing_role` |
| `GET` | `/api/tenant-setup/halls` | TenantApp | `venue_layout.list_halls` | Tenant Admin session | Query: `includeDisabled?` | `HallList` | `not_authorized` |
| `POST` | `/api/tenant-setup/halls` | TenantApp | `venue_layout.create_hall` | Tenant Admin session + CSRF | Body: `HallWriteRequest` | `Hall` | `duplicate_hall`, `validation_failed` |
| `PATCH` | `/api/tenant-setup/halls/{hallId}` | TenantApp | `venue_layout.update_hall` | Tenant Admin session + CSRF | Body: editable hall fields | `Hall` | `duplicate_hall`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/halls/{hallId}/disable` | TenantApp | `venue_layout.disable_hall` | Tenant Admin session + CSRF | Body: `reason` | `Hall` | `active_session_blocks_disable`, `reason_required` |
| `POST` | `/api/tenant-setup/halls/{hallId}/tables` | TenantApp | `venue_layout.create_table` | Tenant Admin session + CSRF | Body: `TableWriteRequest` | `Table` | `duplicate_table`, `validation_failed` |
| `PATCH` | `/api/tenant-setup/tables/{tableId}` | TenantApp | `venue_layout.update_table` | Tenant Admin session + CSRF | Body: editable table fields | `Table` | `duplicate_table`, `active_session_blocks_disable` |
| `POST` | `/api/tenant-setup/tables/{tableId}/disable` | TenantApp | `venue_layout.disable_table` | Tenant Admin session + CSRF | Body: `reason` | `Table` | `active_session_blocks_disable`, `reason_required` |
| `GET` | `/api/tenant-setup/tables/{tableId}/context` | TenantApp | `venue_layout.get_table_context` | Tenant Admin session | Path: `tableId` | `TableContext` | `not_found_or_hidden` |

## Request Schemas

`HallWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Unique in tenant. |
| `displayOrder` | integer | yes | Unique in tenant. |
| `tableNumberBase` | integer | no | Assigned by backend from hall order/range. The first hall starts at `100`, then `200`, `300`, and so on. |

`TableWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Unique inside hall. |
| `displayOrder` | integer | yes | Unique inside hall. |
| `tableNumber` | integer | no | Assigned by backend from the hall's 100-slot range. |
| `mode` | string | no | `virtual_test` or `physical`; promotion to `physical` is forbidden for `x00` and `x99`. |
| `hallId` | string | no on create path, yes when moving | Moving hall preserves runtime history. |
| `enabled` | boolean | no | Disable command is preferred when reason is required. |

## Response Schemas

`HallTableBoard`:

| Field | Type | Notes |
| --- | --- | --- |
| `halls` | array of `HallWithTables` | Ordered by `displayOrder`. |
| `derivedAt` | timestamp | Read model time. |

`HallWithTables` includes `hallId`, `name`, `displayOrder`, `tableNumberBase`, `enabled`, and ordered `tables`.

`Table` includes `tableId`, `hallId`, `tableNumber`, `name`, `displayOrder`, `mode`, `systemBoundarySlot`, and `enabled`.

`CashierHallTableBoard` uses the same hall/table envelope and adds caller-specific `CashierTableState` per table when available. By default it excludes `virtual_test` tables. It includes them only when `includeVirtualTestTables=true` for the current request. `CashierTableState` may include `activeSessionId?`, `checkId?`, `sessionStatus?`, `totalMinor?`, `paidMinor?`, `remainingMinor?`, `latestOrderState?`, `attentionFlags`, and `derivedAt`.

`CashierTableState` is a derived read model for the cashier board. Venue Layout may compose it for display, but it does not own TableSession, order, fulfillment, Check, or payment state.

## Idempotency

Create/update/disable endpoints do not require `Idempotency-Key`. Hall creation atomically creates exactly 100 table slots in that hall's range. Duplicate halls/tables are blocked by tenant/hall unique constraints. Disable commands and virtual-to-physical promotion are state-guarded and audited.
