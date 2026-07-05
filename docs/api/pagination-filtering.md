# API Pagination and Filtering Standards

This document defines shared rules for list endpoints.

## Pagination Style

Use cursor pagination for the current release list endpoints that can grow or change while users are viewing them.

Query parameters:

| Parameter | Rule |
| --- | --- |
| `limit` | Optional. Default `50`. Maximum `100`. |
| `cursor` | Optional opaque cursor from previous response. |

Response:

```json
{
  "items": [],
  "page": {
    "limit": 50,
    "nextCursor": null,
    "hasMore": false
  }
}
```

Cursors are opaque. Clients must not parse or construct them.

## Stable Ordering

Every paginated query must define deterministic ordering.

Preferred order:

```text
createdAt desc, id desc
```

For operational queues, use the domain-relevant timestamp:

| Queue/List | Preferred Order |
| --- | --- |
| Station queue | oldest pending/active work first |
| Service ready queue | oldest ready item first |
| Payments | `receivedAt desc, id desc` |
| Audit | `createdAt desc, id desc` |
| Tenant list | `createdAt desc, id desc` |

## Filtering

Filters must be explicit and allowlisted per endpoint.

Common filter naming:

| Filter | Meaning |
| --- | --- |
| `status` | Exact status enum. |
| `from` / `to` | Time range where endpoint context makes the timestamp obvious. |
| `createdFrom` / `createdTo` | Creation time range. |
| `updatedFrom` / `updatedTo` | Update time range. |
| `stationId` | Station-scoped list filter. |
| `hallId` | Hall-scoped list filter. |
| `tableId` | Table-scoped list filter. |
| `q` | Human search text, only where explicitly supported. |

Do not accept arbitrary database column names from clients.

## Sorting

If custom sorting is needed, use:

```text
sort=<allowlisted-field>
direction=asc|desc
```

Rules:

- Every sortable field must be documented in the endpoint contract.
- Sorting must preserve a stable tie-breaker such as `id`.
- Do not allow sorting by secret/internal/security fields.

## Offset Pagination

Offset pagination is not the default.

It may be used only for small, stable setup lists where:

- the list is tenant-scoped;
- item count is naturally small;
- ordering is deterministic;
- endpoint contract explicitly allows it.

Runtime lists such as orders, payments, audit events, station queues, and side-effect attempts must use cursor pagination.

## Empty Lists

Empty list responses return:

```json
{
  "items": [],
  "page": {
    "limit": 50,
    "nextCursor": null,
    "hasMore": false
  }
}
```

Do not return `404` for an empty list.

## Authorization and Filtering

Authorization is applied before or together with filtering.

Examples:

- StationStaffApp may only list assigned stations, even if it supplies another `stationId`.
- ServiceStaffApp may only list assigned halls.
- CustomerApp table-order visibility requires fresh presence before filters matter.
- PlatformApp tenant lists must not expose tenant runtime detail through filters.
