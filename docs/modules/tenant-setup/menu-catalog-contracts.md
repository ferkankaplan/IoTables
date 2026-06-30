# Module Contracts: Menu Catalog

Source module: [menu-catalog.md](menu-catalog.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `menu_catalog.create_category` | TenantApp, Provisioning | tenantId, name, displayOrder | Tenant Admin/Provisioning; unique name/order | Insert category; audit for TenantApp changes | Menu category |
| `menu_catalog.update_category` | TenantApp | categoryId, editable fields | Tenant Admin own tenant | Update category | Updated category |
| `menu_catalog.disable_category` | TenantApp | categoryId, reason | Tenant Admin; disabled category hides orderable products | Set enabled false; preserve history | Disabled category |
| `menu_catalog.create_product_service` | TenantApp, Provisioning | categoryId, stationId, name, description, variants | Tenant Admin/Provisioning; station/category same tenant; at least one valid variant for enabled product | Insert product and variants atomically | Product/service |
| `menu_catalog.update_product_service` | TenantApp | productId, editable fields, stationId | Tenant Admin; station same tenant; current orders keep snapshots | Update product config; no historical price rewrite | Updated product/service |
| `menu_catalog.disable_product_service` | TenantApp | productId, reason | Tenant Admin | Set enabled false; preserve order history | Disabled product/service |
| `menu_catalog.manage_variant` | TenantApp, Provisioning | productId, name, priceMinor, default/enabled/order | Tenant Admin/Provisioning; price non-negative; one default variant | Upsert variant; current orders unaffected | Product variant |
| `menu_catalog.manage_modifiers` | TenantApp, Provisioning | productId, groups/options | Tenant Admin/Provisioning; selection bounds valid; deltas non-negative in v1 | Upsert modifier config | Modifier groups/options |
| `menu_catalog.set_availability` | TenantApp | productId, optional variantId, state, reason, window | Tenant Admin; target belongs to tenant/product; window valid | Insert availability override | Availability override |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `menu_catalog.list_menu_setup` | TenantApp | tenantId, includeDisabled flag | Tenant Admin own tenant | Categories, products/services, variants, modifiers, availability, and station assignments for setup UI |
| `menu_catalog.get_product_service` | TenantApp, CashierApp, StationStaffApp | productId | Tenant/staff read scope appropriate to caller | Product/service detail with variants, modifiers, availability, and station assignment |
| `menu_catalog.get_customer_menu` | CustomerApp | tenantId, table/customer session context | Tenant active; only enabled/orderable/available items | Customer-visible menu categories/products/variants/modifiers |
| `menu_catalog.validate_cart_item` | Customer Ordering | tenantId, productId, variantId, modifiers, quantity | Product/variant enabled, available, station enabled, modifiers valid | Validated item with server price inputs |
| `menu_catalog.price_cart_item` | Customer Ordering | cart item selection | Server-side only; frontend price ignored | Price snapshot components |
| `menu_catalog.read_order_item_routing` | Ordering, Fulfillment | productId/variantId | Internal module call | Station routing and product labels for snapshot |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `station_setup.get_station_context` | Validate station routing. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `menu_catalog.changed` | Category/product/variant/modifier changes | Customer menu cache/read models, Audit |
| `availability.changed` | Availability override changes | CustomerApp menu, order validation |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_category` | Category name/order conflicts inside tenant. |
| `product_not_orderable` | Product disabled, unavailable, or missing enabled variant. |
| `variant_invalid` | Variant disabled or not under selected product. |
| `station_unavailable` | Product routes to disabled/missing station. |
| `client_price_ignored` | Client supplied price cannot affect order snapshot. |
