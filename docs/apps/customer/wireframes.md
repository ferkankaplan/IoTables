# CustomerApp Wireframes

CustomerApp wireframes define the customer-facing ordering workspace. They describe the visible product flow, not React component APIs, CSS, database ownership, or backend contracts.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../_shared/wireframe-rules.md](../_shared/wireframe-rules.md)
- [../_shared/component-model.md](../_shared/component-model.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Route and Workspace Decision

CustomerApp lives on the tenant host:

```text
https://[tenant].iotables.net/order
```

The QR displayed on the table screen opens the same Customer Order Workspace and carries only the redemption material needed by the backend table-presence endpoint. The route itself is not trusted authority. Tenant, table, session, pricing, station routing, and table-session authority are always resolved server-side.

Durable UI views may use query state such as:

| UI View | Example URL | Purpose |
| --- | --- | --- |
| Menu | `/order` | Main customer workspace after valid QR redemption. |
| My Orders | `/order?view=my-orders` | Orders from the current CustomerOrderingSession. |
| Table Orders | `/order?view=table-orders` | Active table orders after fresh presence. |
| Bill | `/order?view=bill` | Read-only bill and balance after fresh presence. |

Query state only selects the visible view. It must not bypass QR redemption, fresh presence, or backend visibility guards.

## Primary Workspace

The Customer Order Workspace keeps menu browsing, cart review, order visibility, and bill visibility in one app context.

```text
+------------------------------------------------+
| Tenant / Table header                          |
| Menu | Siparislerim | Masa Siparisleri | Hesap |
+------------------------------------------------+
| Category rail / tabs                           |
+------------------------------------------------+
| Product list                                   |
|                                                |
| [Product card] [Product card] [Product card]   |
|                                                |
+------------------------------------------------+
| Fixed cart action bar                          |
+------------------------------------------------+
```

Visible regions map to shared components:

| Region | Component Responsibility |
| --- | --- |
| Tenant/table header | `TableContextHeader` |
| Presence and retry gate | `QrPresenceGate` |
| Category/product browsing | `MenuCatalog` |
| Product detail overlay | `ProductDetailSheet` |
| Cart summary and submit entry | `CartActionBar` |
| Cart review and edit | `CartSheet` |
| Confirmation state | `OrderConfirmation` |
| My Orders and Table Orders | `CustomerOrdersView` |
| Bill and balance | `ReadOnlyBillSummary` |

## QR Entry and Presence Gate

QR redemption is the first visible gate when the customer opens the workspace from a table QR.

Default flow:

1. Show a compact loading state while the token is redeemed.
2. On success, show table context and open the menu.
3. On recoverable failure, show a retry state asking the customer to scan the current table QR.
4. If a cart exists and fresh presence expires, preserve the cart and return the customer to the cart after successful re-verification.

Required states:

| State | Wireframe Behavior |
| --- | --- |
| Loading | Keep a stable shell with tenant-safe identity if available. |
| QR expired | Show current-QR retry message. |
| QR already used | Show current-QR retry message. |
| Wrong table | Tell the customer to scan their own table QR. |
| Tenant unavailable | Show unavailable state and no ordering controls. |
| Table unavailable | Show table unavailable state and no ordering controls. |
| Browser cannot keep session | Allow only non-ordering preview if supported; disable cart submit. |

The gate must not show token values, table IDs, session IDs, credential state, or technical security names.

## Menu View

Menu is the default workspace after a successful QR redemption or valid returning customer session.

Required layout:

- tenant/table context remains visible;
- categories are easy to scan and switch;
- product cards show image or fallback, name, short description when available, availability, and visible price;
- unavailable products or variants are visibly blocked and not orderable;
- cart action bar stays reachable without covering content.

Product card minimum fields:

| Field | Notes |
| --- | --- |
| Image/fallback | Missing image must render as polished fallback. |
| Name | Customer-facing product/service name. |
| Description | Short and optional. |
| Price | Display price only; backend remains authority. |
| Availability | Visible only when blocked or useful. |
| Add/open action | Opens product detail when options exist; direct add only when valid defaults exist. |

Menu states:

| State | Wireframe Behavior |
| --- | --- |
| Loading | Keep table header and category skeleton stable. |
| Empty menu | Show no orderable items; do not expose admin configuration. |
| Category empty | Keep category tabs and show empty state inside selected category. |
| Product unavailable | Product visible only if useful, with disabled add action. |
| Variant unavailable | Variant is disabled in product detail. |
| Image missing | Fallback visual preserves card size. |

## Product Detail Sheet

Selecting a product opens a contextual sheet or panel instead of navigating away from the menu.

The sheet contains:

- product image/fallback;
- full name and description;
- variant or portion selector when more than one orderable variant exists;
- required modifier groups;
- optional modifier groups;
- quantity stepper;
- per-item note;
- estimated item total;
- add-to-cart action.

Validation behavior:

| Case | Behavior |
| --- | --- |
| Required variant missing | Add-to-cart disabled; missing group is highlighted. |
| Required modifier missing | Add-to-cart disabled; missing group is highlighted. |
| Invalid combination | Keep sheet open and point to affected choice. |
| Option unavailable | Disable the option and explain it is not orderable. |
| Add pending | Disable add action until backend cart update returns. |

On successful add-to-cart, CustomerApp stays in menu context. The sheet may close or stay open only if the next natural action is clear.

## Cart Sheet and Action Bar

The fixed action bar shows the cart count and estimated subtotal when the cart is not empty. It opens the cart sheet.

Cart sheet content:

- item list with product, variant, modifiers, note, quantity, and estimated price;
- edit item action that reopens product detail in edit mode;
- remove item action;
- subtotal estimate;
- freshness requirement state;
- submit order action.

Cart states:

| State | Behavior |
| --- | --- |
| Empty | Keep customer in menu; no separate empty page. |
| Editable | Quantity, note, modifier, and remove controls are available. |
| Stale item | Highlight affected item and require edit/remove. |
| Invalid item | Open item editor from the error. |
| Fresh presence expired | Preserve cart and ask for current QR before submit. |
| Submitting | Disable submit and item mutation controls; keep summary visible. |
| Network failure after submit | Retry with the same idempotency key; do not create a second visible order. |
| Duplicate submit replay | Show original accepted result as confirmation. |

Order submit is a mutating action and must show pending state, backend failure state, duplicate replay state, and cart-preservation behavior.

## Order Confirmation

Order confirmation appears only after backend acceptance or an idempotent replay of an already accepted order.

It shows:

- accepted message;
- submitted order summary;
- item quantities;
- selected modifiers;
- item notes;
- mapped customer-visible status;
- action to return to menu;
- action to view My Orders.

It must not imply payment, cancellation, refund, discount, or order editing is available.

## My Orders

My Orders shows orders submitted by the current CustomerOrderingSession.

Layout:

- order groups sorted newest first;
- each order shows order time, item list, item notes where customer-visible, visible price snapshots, and customer-readable status;
- empty state says there are no orders from this browser yet.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep nav and table context stable. |
| Empty | Show no orders from this browser/session. |
| Session lost | Ask customer to scan the table QR again; do not promise old My Orders recovery. |

If the same browser orders tea now and again later within the same CustomerOrderingSession, both submitted orders appear here.

## Table Orders

Table Orders shows all orders attached to the active TableSession for the table. It requires fresh table presence.

Layout:

- fresh presence gate appears before data loads if needed;
- order groups show order time, item list, quantity, item notes, visible price snapshots, and mapped status;
- no edit, cancel, payment, discount, refund, or close controls appear.

States:

| State | Behavior |
| --- | --- |
| Fresh presence required | Ask customer to scan the current QR. |
| Loading | Keep nav and table context stable. |
| Empty active session | Show no active table orders after verification. |
| Active orders visible | Read-only list of table-session orders. |
| TableSession closed | Do not mutate; new order requires current table QR and current table state. |

Table Orders can recover visibility after browser cookie loss only after a fresh QR scan.

## Bill and Balance

Bill shows read-only table-session billing information after fresh presence.

Required content:

- table total;
- paid amount;
- remaining balance;
- order totals;
- order times;
- item-level prices;
- customer-readable item status;
- payment/balance update state.

Forbidden controls:

- pay;
- mark paid;
- close table session;
- discount;
- refund;
- cancel item;
- edit submitted order;
- fiscal receipt or e-Adisyon creation.

Bill states:

| State | Behavior |
| --- | --- |
| Fresh presence required | Ask customer to scan current QR. |
| Loading | Keep the Bill tab selected and show stable summary skeleton. |
| Read-only balance | Show server-calculated totals and no mutation controls. |
| Payment updated | Refresh visible paid/remaining state without implying customer action. |

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Primary target. Bottom navigation or compact tabs, product detail and cart as bottom sheets, fixed safe cart action bar. |
| Tablet | Menu can use two columns; detail/cart may become side drawer when space allows. |
| Desktop | Wider menu grid with optional cart/detail side context; still a customer workspace, not an admin dashboard. |

No text may depend on viewport-width font scaling. Long product names, modifier labels, and price rows must wrap inside stable containers without overlapping action controls.

## Accessibility

- The full order path must work by keyboard.
- Bottom sheets and drawers must trap focus while open and restore focus to the triggering control on close.
- Required variant/modifier errors need visible text, not color alone.
- Fixed action bars must not cover content at the bottom of mobile screens.
- Touch targets for add, quantity, remove, tabs, and submit controls must be comfortable for one-handed mobile use.
- Status labels such as `Hazırlanıyor` and `Teslim edildi` must be readable by assistive technology.

## Data Visibility Boundaries

CustomerApp may show only the fields allowed by [visibility.md](visibility.md).

Never show:

- raw tenant/table IDs as authority;
- QR token values;
- CustomerOrderingSession IDs;
- TableSession IDs;
- display credential state;
- station routing internals;
- cashier-only notes;
- staff data;
- payment mutation controls;
- stack traces or API internals.

## V1 Out-of-Scope UI

The following UI must not appear in CustomerApp v1:

- pay-at-table;
- payment provider checkout;
- cancel submitted order;
- edit submitted order;
- request refund;
- request discount;
- split bill or split item payment;
- close table session;
- fiscal receipt/e-Adisyon/ÖKC controls;
- staff login, tenant setup, station queue, service delivery, or cashier controls.

## Acceptance Check

This wireframe package is valid when:

- every CustomerApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- every mutating customer action has pending and failure behavior;
- duplicate submit shows the original accepted result;
- cart-preserving fresh QR verification is visible;
- no forbidden v1 control appears.
