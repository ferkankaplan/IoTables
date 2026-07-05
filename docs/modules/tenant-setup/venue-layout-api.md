# API Contracts: Venue Layout

Source contracts: [venue-layout-contracts.md](venue-layout-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Venue Layout owns halls, tables, ordered display, and table context. It does not own orders, sessions, payments, or fulfillment state.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/tenant-setup/venue/board` | TenantApp | `venue_layout.get_hall_table_board` | Tenant Admin session | none | `HallTableBoard` | `not_authorized` |
| `GET` | `/api/cashier/venue/board` | CashierApp | `venue_layout.get_hall_table_board` | Cashier session | none | `CashierHallTableBoard` | `missing_role` |
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

`TableWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | Unique inside hall. |
| `displayOrder` | integer | yes | Unique inside hall. |
| `hallId` | string | no on create path, yes when moving | Moving hall preserves runtime history. |
| `enabled` | boolean | no | Disable command is preferred when reason is required. |

## Response Schemas

`HallTableBoard`:

| Field | Type | Notes |
| --- | --- | --- |
| `halls` | array of `HallWithTables` | Ordered by `displayOrder`. |
| `derivedAt` | timestamp | Read model time. |

`HallWithTables` includes `hallId`, `name`, `displayOrder`, `enabled`, and ordered `tables`.

`Table` includes `tableId`, `hallId`, `name`, `displayOrder`, and `enabled`.

`CashierHallTableBoard` uses the same hall/table envelope and adds caller-specific `CashierTableState` per table when available. `CashierTableState` may include `activeSessionId?`, `checkId?`, `sessionStatus?`, `totalMinor?`, `paidMinor?`, `remainingMinor?`, `latestOrderState?`, `attentionFlags`, and `derivedAt`.

`CashierTableState` is a derived read model for the cashier board. Venue Layout may compose it for display, but it does not own TableSession, order, fulfillment, Check, or payment state.

## Idempotency

Create/update/disable endpoints do not require `Idempotency-Key`. Duplicate halls/tables are blocked by tenant/hall unique constraints. Disable commands are state-guarded and audited.
