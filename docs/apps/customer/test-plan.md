# CustomerApp Test Plan

This document defines CustomerApp-visible test coverage for the current release. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

Source context:

- [definition.md](definition.md)
- [end-to-end.md](end-to-end.md)
- [scenarios.md](scenarios.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [wireframes.md](wireframes.md)
- [copy.md](copy.md)
- [components.md](components.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Test Scope

CustomerApp tests prove that an anonymous customer can scan a table QR, browse the menu, build a cart, submit orders safely, inspect own/table orders, and read a bill summary without gaining staff or payment mutation authority.

Out of scope for this test plan:

- station preparation mutation;
- service delivery mutation;
- cashier payment/correction/session-close mutation;
- tenant setup;
- platform tenant creation;
- payment provider checkout;
- fiscal/e-Adisyon/ÖKC behavior.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| C-01 Redeem Fresh QR | Fresh QR opens `/order`, creates or refreshes CustomerOrderingSession, and shows menu with table context. |
| C-02 Browse Menu and Build Cart | Customer browses categories, opens product detail, selects required options, adds to cart, edits quantity/note/options. |
| C-03 Submit First Order at Empty Table | Submit creates first TableSession/Check/order atomically, clears submitted cart, and shows confirmation. |
| C-04 Submit Additional Order at Active Table | Same session can submit another order; My Orders shows both; Table Orders shows active table orders after fresh presence. |
| C-05 View My Orders, Table Orders, and Bill | Customer reads own orders, fresh-verifies for table orders/bill, and sees read-only balance. |

## Branch Coverage

### QR and Presence

| Branch | Expected Test Result |
| --- | --- |
| Expired QR | Fail closed with current-QR retry copy. |
| Already consumed QR | Fail closed with current-QR retry copy. |
| Wrong-table QR | Does not change current customer context or cart; asks for own table QR. |
| Concurrent redemption | Only one redemption succeeds; failed attempts show retry safely. |
| Fresh presence expired before submit | Cart is preserved and submit is blocked until current QR succeeds. |
| Browser rejects or loses cookie | Ordering cannot proceed without a new valid QR; Table Orders may recover after fresh QR. |

### Menu and Cart

| Branch | Expected Test Result |
| --- | --- |
| Empty menu | Shows customer-safe empty state with no admin internals. |
| Product unavailable | Product cannot be added to cart. |
| Variant unavailable | Variant cannot be selected for ordering. |
| Required variant missing | Add-to-cart blocked with field-level message. |
| Required modifier missing | Add-to-cart blocked with field-level message. |
| Invalid modifier combination | Add-to-cart blocked and affected group is visible. |
| Stale cart item at submit | Submit rejected, cart preserved, affected item highlighted. |
| Menu reload while cart exists | Cart remains tied to CustomerOrderingSession while valid. |

### Order Submission

| Branch | Expected Test Result |
| --- | --- |
| Empty cart submit | Submit rejected and no order created. |
| Duplicate submit same idempotency key and same request | Original accepted result is shown; no duplicate order. |
| Duplicate submit same idempotency key and different request | Conflict is shown safely; no duplicate or partial order. |
| Network failure after submit | Retry uses same submit attempt; no duplicate visible order. |
| Concurrent first order at table | One active TableSession exists; order attaches to current active TableSession. |
| TableSession closes before submit | Requires current QR and current table state; closed session is not mutated. |
| Transaction failure during submit | No partial order, Check, PreparationItem, station queue item, customer history, or cashier-visible record appears. |

### Order, Table, and Bill Visibility

| Branch | Expected Test Result |
| --- | --- |
| Same CustomerOrderingSession submits multiple orders | My Orders shows all orders from that session. |
| Different browser at same table submits order | First browser My Orders excludes it; Table Orders includes it after fresh presence. |
| Cookie lost | My Orders continuity may be lost; Table Orders can recover after fresh QR. |
| Payment recorded by cashier | Bill summary updates read-only. |
| Payment voided by cashier | Bill summary updates read-only. |
| Item voided by cashier | Order/bill state updates read-only with no customer mutation controls. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Fresh QR reaches menu | Browser E2E with QR redemption and menu visible. |
| Expired/reused/wrong-table QR fail safely | API/security tests plus UI copy tests. |
| Cart survives fresh QR re-verification | Browser E2E keeps cart after presence retry. |
| Required variants/modifiers block add-to-cart | Component and browser tests. |
| Unavailable products/variants are not orderable | Component, API, and E2E tests. |
| Submit requires fresh table presence | API contract and browser E2E. |
| Duplicate submit does not create duplicate orders | API idempotency and browser retry tests. |
| Failed submit keeps cart editable | Browser and component tests. |
| Successful submit clears only submitted cart | Browser E2E. |
| My Orders shows multiple same-session orders | Browser E2E. |
| Table Orders requires fresh presence | Browser and API tests. |
| Bill/balance requires fresh presence and is server-calculated | API and browser tests. |
| Customers cannot pay/close/cancel/discount/refund/edit | Negative UI and API authorization tests. |
| Visible statuses match service tracking mode | Domain mapping and UI tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| QR Entry / Session Start | loading, QR expired, QR already used, wrong table, tenant unavailable, table unavailable |
| Menu | loading, empty menu, category empty, product unavailable, variant unavailable, image missing fallback |
| Product Detail | loading, required variant missing, required modifier missing, invalid combination, unavailable option |
| Cart | empty cart, editable cart, stale item, invalid item, fresh presence expired, submitting |
| Order Confirmation | accepted, duplicate submit returned, submit failed preserving cart |
| My Orders | loading, empty, session expired/lost |
| Table Orders | fresh presence required, loading, empty active session, active orders visible |
| Bill / Balance | fresh presence required, loading, read-only balance, payment updated |

## API Usage Coverage

CustomerApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/tenant/context` | Tenant active/unavailable display; no sensitive tenant internals. |
| `GET /api/customer/menu` | Only orderable customer-visible menu data; unavailable handling. |
| `POST /api/customer/table-presence/redeem` | Expired, consumed, wrong-table, concurrent, and success cases. |
| `GET /api/customer/table-presence` | Fresh and expired presence states. |
| `GET /api/customer/cart` | Own session only; empty and populated cart. |
| `POST /api/customer/cart/items` | Valid item, invalid variant/modifier, unavailable item, CSRF failure. |
| `POST /api/customer/cart/items/{clientCartItemId}/remove` | Own cart item removal and missing item behavior. |
| `POST /api/customer/orders` | Fresh presence, idempotency, duplicate replay, conflict, stale cart, rollback. |
| `GET /api/customer/orders/my` | Same CustomerOrderingSession scope only. |
| `GET /api/customer/table-orders` | Fresh presence required; active TableSession order visibility. |
| `GET /api/customer/table-session` | Fresh presence required; read-only active table state. |
| `GET /api/customer/table-session/bill-summary` | Server-calculated bill; no mutation fields. |
| `GET /api/customer/table-session/payment-summary` | Paid/remaining only; no payment mutation affordance. |

## Security and Abuse Coverage

Required tests:

- raw QR token is never shown after redemption failure;
- client-supplied tenant, table, station, TableSession, price, subtotal, or total values are ignored;
- cross-tenant host/body mismatch fails closed;
- wrong-table token does not move an existing cart;
- expired fresh presence blocks submit, table orders, bill summary, and payment summary;
- CSRF is required for unsafe cookie-auth CustomerApp requests;
- rate-limited QR/order abuse shows safe copy;
- staff, cashier, tenant admin, and platform APIs are not reachable from CustomerApp session authority;
- no raw secrets, stack traces, internal paths, or IDs are exposed in customer responses.

## Accessibility and Responsive Coverage

Required checks:

- complete scan-to-order path works by keyboard;
- bottom sheets and drawers trap and restore focus;
- fixed cart action bar does not cover content on mobile;
- product names, modifier labels, prices, and error text wrap without overlap on small mobile, tablet, and desktop;
- touch targets for quantity, add, remove, retry QR, tabs, and submit are usable;
- required choices and errors are announced with text, not color alone;
- status labels are accessible as text.

## Copy Coverage

Tests must assert that:

- customer-facing QR failures use [copy.md](copy.md);
- order accepted copy appears only after backend acceptance or accepted replay;
- submit failure copy states cart preservation when applicable;
- CustomerApp UI does not show forbidden technical terms from [copy.md](copy.md);
- CustomerApp UI does not show forbidden current release action labels.

## Forbidden Control Coverage

CustomerApp tests must prove these controls are absent:

- payment creation or provider checkout;
- close table session;
- cancel submitted order;
- edit submitted order;
- refund;
- discount;
- fiscal receipt/e-Adisyon/ÖKC;
- staff login or staff queue actions;
- tenant setup;
- platform tenant management.

## Traceability

When implementation begins:

- browser E2E tests should reference CustomerApp scenarios C-01 through C-05;
- API tests should reference [api-usage.md](api-usage.md) and module API contracts;
- race and rollback tests should reference transaction and idempotency sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

CustomerApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- QR/presence/order idempotency abuse coverage is defined;
- UI state and copy coverage are defined;
- forbidden CustomerApp controls are explicitly tested absent;
- semantic index is regenerated after this document changes.
