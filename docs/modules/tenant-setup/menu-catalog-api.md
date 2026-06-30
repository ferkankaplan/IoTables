# API Contracts: Menu Catalog

Source contracts: [menu-catalog-contracts.md](menu-catalog-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Menu Catalog owns categories, products/services, variants, modifiers, availability, and product-to-station routing.

Customer prices are display estimates. Order submission always revalidates and prices server-side.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/customer/menu` | CustomerApp | `menu_catalog.get_customer_menu` | Customer session optional; tenant active | Host-derived tenant | `CustomerMenu` | `tenant_unavailable` |
| `GET` | `/api/v1/tenant-setup/menu` | TenantApp | `menu_catalog.list_menu_setup` | Tenant Admin session | Query: `includeDisabled?` | `MenuSetupCatalog` | `not_authorized` |
| `GET` | `/api/v1/tenant-setup/menu/products/{productId}` | TenantApp | `menu_catalog.get_product_service` | Tenant Admin session | Path: `productId` | `ProductService` | `not_found_or_hidden` |
| `POST` | `/api/v1/tenant-setup/menu/categories` | TenantApp | `menu_catalog.create_category` | Tenant Admin session + CSRF | Body: `CategoryWriteRequest` | `Category` | `duplicate_category`, `validation_failed` |
| `PATCH` | `/api/v1/tenant-setup/menu/categories/{categoryId}` | TenantApp | `menu_catalog.update_category` | Tenant Admin session + CSRF | Body: editable category fields | `Category` | `not_found_or_hidden`, `validation_failed` |
| `POST` | `/api/v1/tenant-setup/menu/categories/{categoryId}/disable` | TenantApp | `menu_catalog.disable_category` | Tenant Admin session + CSRF | Body: `reason` | `Category` | `reason_required` |
| `POST` | `/api/v1/tenant-setup/menu/products` | TenantApp | `menu_catalog.create_product_service` | Tenant Admin session + CSRF | Body: `ProductWriteRequest` | `ProductService` | `station_unavailable`, `validation_failed` |
| `PATCH` | `/api/v1/tenant-setup/menu/products/{productId}` | TenantApp | `menu_catalog.update_product_service` | Tenant Admin session + CSRF | Body: editable product fields | `ProductService` | `station_unavailable`, `validation_failed` |
| `POST` | `/api/v1/tenant-setup/menu/products/{productId}/disable` | TenantApp | `menu_catalog.disable_product_service` | Tenant Admin session + CSRF | Body: `reason` | `ProductService` | `reason_required` |
| `POST` | `/api/v1/tenant-setup/menu/products/{productId}/variants` | TenantApp | `menu_catalog.manage_variant` | Tenant Admin session + CSRF | Body: `VariantWriteRequest` | `ProductVariant` | `validation_failed` |
| `POST` | `/api/v1/tenant-setup/menu/products/{productId}/modifiers` | TenantApp | `menu_catalog.manage_modifiers` | Tenant Admin session + CSRF | Body: `ModifierConfigRequest` | `ModifierConfig` | `validation_failed` |
| `POST` | `/api/v1/tenant-setup/menu/products/{productId}/availability` | TenantApp | `menu_catalog.set_availability` | Tenant Admin session + CSRF | Body: `AvailabilityRequest` | `AvailabilityOverride` | `validation_failed` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `menu_catalog.validate_cart_item` | Called by Customer Ordering during cart mutation and order submission. |
| `menu_catalog.price_cart_item` | Called by Customer Ordering server-side; frontend price is ignored. |
| `menu_catalog.read_order_item_routing` | Called by Ordering/Fulfillment. |

## Request Schemas

`CategoryWriteRequest` includes `name`, `displayOrder`, and optional `enabled`.

`ProductWriteRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `categoryId` | string | yes | Category must belong to tenant. |
| `stationId` | string | yes | Station must belong to tenant and be enabled for orderable products. |
| `name` | string | yes | Customer-visible name. |
| `description` | string | no | Customer-visible description. |
| `variants` | array | yes on create | At least one valid enabled/default variant for enabled product. |
| `modifierGroups` | array | no | Selection bounds validated. |

`VariantWriteRequest` includes `variantId?`, `name`, `priceMinor`, `currency`, `isDefault`, `enabled`, and `displayOrder`.

`AvailabilityRequest` includes `variantId?`, `state`, `reason`, `startsAt?`, and `endsAt?`.

## Response Schemas

`MenuSetupCatalog` includes categories, products/services, variants, modifier groups/options, availability overrides, and station assignments needed by TenantApp menu management.

`CustomerMenu` includes ordered categories and only enabled/orderable/available products, variants, modifiers, station-hidden routing, and display prices in minor units.

`ProductService` includes `productId`, `categoryId`, `stationId`, `name`, `description`, `enabled`, `variants`, `modifierGroups`, `availability`, `createdAt`, and `updatedAt`.

## Idempotency

Menu setup endpoints do not require `Idempotency-Key`. They rely on validation, unique setup constraints, and audit. Customer order submission owns duplicate-submit protection.
