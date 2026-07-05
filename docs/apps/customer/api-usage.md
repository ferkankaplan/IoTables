# CustomerApp API Usage

CustomerApp uses tenant-scoped APIs on `https://[tenant].iotables.net`.

CustomerApp does not use human Identity and Access. It uses an anonymous CustomerOrderingSession cookie plus fresh QR presence where required.

## API Map

| App Need | Endpoint | Module API Contract | Notes |
| --- | --- | --- | --- |
| Tenant context | `GET /api/tenant/context` | [Tenant Registry](../../modules/platform/tenant-registry-api.md) | Safe tenant display/availability only. |
| Menu browsing | `GET /api/customer/menu` | [Menu Catalog](../../modules/tenant-setup/menu-catalog-api.md) | Public tenant-active read; order submit revalidates. |
| Redeem QR | `POST /api/customer/table-presence/redeem` | [Table Presence](../../modules/ordering/table-presence-api.md) | Sets/refreshes CustomerOrderingSession cookie. |
| Presence state | `GET /api/customer/table-presence` | [Table Presence](../../modules/ordering/table-presence-api.md) | Shows fresh presence expiry/table context. |
| Cart read | `GET /api/customer/cart` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Own anonymous session only. |
| Cart mutate | `POST /api/customer/cart/items`, `POST /api/customer/cart/items/{clientCartItemId}/remove` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Server validates menu; client price ignored. |
| Submit order | `POST /api/customer/orders` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Requires fresh presence and `Idempotency-Key`. |
| My orders | `GET /api/customer/orders/my` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | All orders from current CustomerOrderingSession. |
| Table orders | `GET /api/customer/table-orders` | [Customer Ordering](../../modules/ordering/customer-ordering-api.md) | Requires fresh presence. |
| Active table session | `GET /api/customer/table-session` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Read-only. |
| Bill summary | `GET /api/customer/table-session/bill-summary` | [Table Session and Billing](../../modules/settlement/table-session-billing-api.md) | Server-calculated totals and timestamps. |
| Payment summary | `GET /api/customer/table-session/payment-summary` | [Payments](../../modules/settlement/payments-api.md) | Paid/remaining summary only. |

## Explicit Non-Usage

CustomerApp cannot mutate submitted orders, payments, corrections, table session closure, preparation, delivery, tenant setup, or staff data.
