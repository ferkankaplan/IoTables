# CustomerApp Components

This document maps CustomerApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

Source context:

- [definition.md](definition.md)
- [wireframes.md](wireframes.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [../_shared/component-model.md](../_shared/component-model.md)
- [../_shared/wireframe-rules.md](../_shared/wireframe-rules.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)

## Component Ownership Rules

- Components own customer-facing responsibilities, not database entities.
- Components may display estimated prices, but they do not own pricing authority.
- Components must preserve table/menu/cart context across panels and sheets.
- Components must not expose internal identifiers, token values, credential state, station routing, or cashier-only data.
- Components must not provide payment, cancellation, refund, discount, close-session, tenant setup, staff, station, or cashier actions in the current release.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `CustomerAppShell` | Tenant host context, `/order` workspace routing, responsive app frame. | Tenant context, presence state |
| `QrPresenceGate` | Redeem QR, refresh presence, show retry states, preserve cart during re-verification. | Table Presence |
| `TableContextHeader` | Customer-safe tenant/table label and current view navigation. | Tenant context, presence state |
| `MenuCatalog` | Category and product browsing with availability and image fallback. | Customer menu |
| `CategoryTabs` | Category selection without leaving menu context. | Customer menu |
| `ProductCard` | Product summary and orderability entry. | Customer menu |
| `ProductDetailSheet` | Variant, modifier, quantity, note, and add-to-cart flow. | Customer menu, cart mutate |
| `ModifierSelector` | Required/optional choice groups with validation state. | Customer menu |
| `QuantityStepper` | Quantity selection with accessible increment/decrement controls. | Product detail, cart |
| `ItemNoteField` | Customer-visible per-item note before submission. | Product detail, cart |
| `CartActionBar` | Fixed cart count/subtotal and cart sheet entry. | Cart read |
| `CartSheet` | Editable cart, stale item handling, and submit entry. | Cart read/mutate, orders |
| `CartItemEditor` | Edit existing cart item choices without losing cart context. | Cart read/mutate, customer menu |
| `SubmitOrderButton` | Pending-safe submit with idempotency-aware visible result. | Submit order |
| `OrderConfirmation` | Accepted order or duplicate replay result. | Submit order, My Orders |
| `CustomerOrdersView` | My Orders and Table Orders read-only lists with mapped statuses. | My orders, table orders |
| `ReadOnlyBillSummary` | Server-calculated total, paid, remaining, and payment summary. | Bill summary, payment summary |
| `CustomerStateMessage` | Empty, loading, blocked, stale, and retry messages. | UI states, copy |

## Shell and Navigation

`CustomerAppShell` owns:

- tenant host context;
- `/order` workspace;
- durable UI view selection;
- responsive layout frame;
- safe unavailable state when tenant cannot serve customers.

It does not own:

- authentication;
- staff roles;
- platform or tenant admin navigation;
- trusted tenant/table authority from client route parameters.

Navigation labels:

- `Menü`
- `Siparişlerim`
- `Masa Siparişleri`
- `Hesap Özeti`

`Table Orders` and `Bill` navigation may open a presence gate before data appears.

## QR Presence Gate

`QrPresenceGate` is used:

- on initial QR landing;
- before order submit when fresh presence expired;
- before Table Orders;
- before Bill and Balance.

Responsibilities:

- submit QR redemption material to the backend;
- show loading, expired, consumed, wrong-table, tenant unavailable, and table unavailable states;
- refresh the existing compatible CustomerOrderingSession when possible;
- preserve cart context while re-verifying;
- return customer to the prior intended surface after successful verification.

Forbidden:

- showing token contents;
- showing session IDs;
- showing credential state;
- moving carts between tenants/tables;
- treating route query values as table authority.

## Menu Components

`MenuCatalog` owns the menu browsing surface.

It contains:

- `CategoryTabs`;
- `ProductCard` list/grid;
- loading skeletons;
- empty menu and empty category states;
- product image fallback states.

`ProductCard` behavior:

| Product Shape | Behavior |
| --- | --- |
| Simple product with valid default variant and no required modifiers | May add directly or open detail if note/quantity is needed. |
| Product with variants or modifiers | Opens `ProductDetailSheet`. |
| Unavailable product | Shows unavailable state and disables ordering. |
| Missing image | Shows stable fallback without layout shift. |

Menu components must not expose station routing or backend validation internals.

## Product Detail Components

`ProductDetailSheet` owns pre-order item configuration.

It uses:

- `ModifierSelector`;
- `QuantityStepper`;
- `ItemNoteField`;
- add/update cart action.

Validation responsibilities:

- block add-to-cart until required variant and modifier selections are valid;
- show item-level error messages;
- keep the sheet open for correctable errors;
- disable submit while cart mutation is pending.

Backend remains responsible for final product, variant, modifier, availability, and price validation.

## Cart Components

`CartActionBar` owns persistent cart entry and estimated subtotal display.

`CartSheet` owns:

- cart item list;
- item edit;
- quantity changes;
- remove item;
- estimated subtotal;
- submit readiness;
- stale/invalid item recovery;
- fresh presence expired state.

`SubmitOrderButton` must:

- generate or reuse the current submit attempt's idempotency key;
- disable while submission is pending;
- show accepted result only after backend acceptance or accepted replay;
- keep cart editable when backend rejects validation;
- preserve cart on network or freshness failure.

Frontend duplicate-submit prevention is required, but backend idempotency remains the authority.

## Order and Bill Components

`OrderConfirmation` displays:

- accepted message;
- submitted item summary;
- visible order time;
- customer-readable status;
- return-to-menu action;
- My Orders action.

`CustomerOrdersView` supports two modes:

| Mode | Data Scope | Fresh Presence |
| --- | --- | --- |
| My Orders | Current CustomerOrderingSession | Not required beyond valid session. |
| Table Orders | Active TableSession for current table | Required. |

It must map internal fulfillment state to `Hazırlanıyor` or `Teslim edildi` according to service tracking mode.

`ReadOnlyBillSummary` displays:

- total;
- paid;
- remaining;
- order totals;
- order times;
- visible payment update state.

It never contains payment, close, refund, discount, fiscal, or correction controls.

## State Components

Use `CustomerStateMessage` for:

- loading;
- empty menu;
- empty cart;
- empty My Orders;
- empty Table Orders;
- fresh QR required;
- tenant unavailable;
- table unavailable;
- stale cart item;
- submit failure;
- duplicate submit replay;
- network retry.

State messages must use [copy.md](copy.md) and must not expose implementation terms.

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Tenant context | Display only safe tenant identity and availability. |
| Table context | Display customer-safe table label only. |
| Menu prices | Display as estimates; backend calculates final order snapshots. |
| Cart | Owned by CustomerOrderingSession; not billable until submit succeeds. |
| Orders | My Orders by CustomerOrderingSession; Table Orders by active TableSession with fresh presence. |
| Bill | Read-only server-calculated summary. |
| Payments | Read-only paid/remaining summary only. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects CustomerApp visibility;
- QR retry and cart preservation are represented;
- duplicate submit behavior is represented;
- order and bill components are read-only after submission;
- forbidden current release actions cannot be reached from any component.
