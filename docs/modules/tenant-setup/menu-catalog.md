# Module: Menu Catalog

## Purpose

Menu Catalog owns tenant menu structure, categories, products/services, variants/portions, prices, availability overrides, modifiers/options, and product-to-station assignment.

It is the pricing and orderability authority for CustomerApp.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Menu category | Entity | create, update, disable |
| Product/service | Entity | create, update, disable |
| Product variant / portion | Entity | define orderable size/portion and current price |
| Price | Value | define current variant price |
| Availability override | State | temporarily mark product or variant unavailable/available |
| Modifier group | Configuration | define required/optional choices |
| Modifier option | Configuration | define choices and price effects |
| Station assignment | Routing config | assign fulfillment station |

## Not Owned

- Customer cart.
- Order item price snapshots after submission.
- Station definitions and lifecycle, owned by Station Setup.
- Station preparation state.
- Payments or bill settlement.
- Staff station permissions.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | manage menu catalog | Own tenant |
| CustomerApp | read menu and product options | Read-only, available items only for ordering |
| CashierApp | read menu/order item context | Read-only |
| StationStaffApp | read product context | Authorized station context |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Manage category | Tenant menu structure | TenantApp |
| Manage product/service | Tenant item setup | TenantApp |
| Manage product variants | Tenant size/portion and current price setup | TenantApp |
| Manage modifiers | Product customization | TenantApp |
| Set availability | Control orderability | TenantApp |
| Get customer menu | Render CustomerApp menu | CustomerApp |
| Validate cart item | Validate selected product, variant, modifiers, and availability | Customer Ordering |
| Price cart item | Server-side price calculation | Customer Ordering |

## Internal Rules

- Current variant prices live here; submitted order price snapshots live in Customer Ordering.
- CustomerApp estimated prices are not authoritative.
- Disabled products remain historical but cannot be ordered.
- Every orderable product/service must have at least one enabled ProductVariant. Simple single-price products use one default variant.
- The selected ProductVariant is required for cart validation and order submission.
- Availability can be product-level or variant-level. Temporary sold-out states use AvailabilityOverride and do not disable catalog history.
- Availability must be rechecked during order submission.
- Required modifiers must be selected before a cart item is valid.
- Product-to-station assignment determines initial preparation routing.
- V1 routes each product/service to exactly one station.
- Multi-station routing for one product/service is out of v1 until a concrete routing workflow exists.
- Product images are referenced by opaque `imageRef` metadata. Menu Catalog owns the reference and display metadata, not binary storage implementation.
- Products without images must remain valid and render with a fallback state in CustomerApp.

## Operational Safety

- Variant price changes must not alter existing order item snapshots.
- Product disabling must not corrupt existing orders.
- Variant disabling must not corrupt existing orders.
- Modifier changes must not invalidate already submitted orders.
- Cart validation must use server-side current catalog data.
- Menu mutations should be audited.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| MenuCategory | Organizes products/services | tenant-scoped |
| ProductService | Menu item/service family | active, description, image |
| ProductVariant | Orderable variant/portion | product, name, price, default flag |
| AvailabilityOverride | Temporary orderability override | product or variant target, state, reason, optional expiry |
| ModifierGroup | Required/optional customization group | min/max selection |
| ModifierOption | Customization option | price delta, availability |
| ProductService.stationId | Fulfillment routing | one station id per product/service in v1 |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Menu management |
| CustomerApp | Menu browsing, product detail, cart |
| CashierApp | Read order item names/prices |
| StationStaffApp | Read station item labels and notes |

## Future Service Boundary

- Own data: categories, products/services, variants/portions, prices, modifiers, availability overrides, ProductService station assignment.
- Own APIs: menu CRUD, customer menu query, cart validation/pricing.
- Published events: product.updated, product.disabled, availability.changed.
- Consumed events: station.disabled, tenant.suspended.
- Must not leak: price authority to frontend.

## Open Questions

None currently.
