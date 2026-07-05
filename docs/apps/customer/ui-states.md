# CustomerApp UI States
### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| QR Entry / Session Start | loading, QR expired, QR already used, wrong table, tenant unavailable, table unavailable |
| Menu | loading, empty menu, category empty, product unavailable, variant unavailable, image missing fallback |
| Product Detail | loading, required variant missing, required modifier missing, invalid combination, unavailable option |
| Cart | empty cart, editable cart, stale item, invalid item, fresh presence expired, submitting |
| Order Confirmation | accepted, duplicate submit returned, submit failed preserving cart |
| My Orders | loading, empty, session expired/lost |
| Table Orders | fresh presence required, loading, empty active session, active orders visible |
| Bill / Balance | fresh presence required, loading, read-only balance, payment updated |

### Empty States

- Empty menu: show no orderable items without exposing admin configuration.
- Empty cart: keep customer in menu context.
- My Orders empty: show no orders from this browser/session.
- Table Orders empty: show no active table orders after fresh QR verification.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| QR expired or already used | Ask customer to scan current QR |
| QR belongs to another table | Ask customer to scan the QR on their own table |
| Fresh presence expired before submit | Preserve cart and require current QR |
| CustomerOrderingSession expired | Create/refresh after valid QR; cart may be lost |
| Product unavailable at submit | Keep cart editable and highlight affected item |
| Variant unavailable at submit | Keep cart editable and highlight affected item |
| Required variant missing | Open affected item editor |
| Modifier invalid at submit | Open affected item editor |
| Tenant suspended | Show tenant unavailable |
| Table disabled or closed to ordering | Reject order and preserve cart where useful |
| Duplicate submit | Show original accepted result, not a second order |
| Network failure after submit | Retry with same idempotency key and avoid duplicate order |

### Success and Confirmation States

- Successful QR redemption opens menu with table context.
- Successful add-to-cart keeps customer in menu/detail context.
- Successful order submit clears only submitted cart and shows order summary.
- Repeat order returns customer to menu and requires fresh presence again at submit.

### Stale and Retry States

- Menu data can become stale; submit must revalidate and return item-level correction states.
- TableSession can close before submit; CustomerApp must require fresh QR and attach only to current valid table state.
- Cookie loss removes My Orders continuity, but Table Orders can recover after fresh QR.

### Visual Priority Rules

- Current table context must be visible without exposing trusted table IDs.
- Cart submit readiness must be obvious when fresh presence has expired.
- Unavailable products, unavailable variants, and invalid cart items must be visible at item level.
- Order confirmation should clearly separate accepted order from editable cart state.

### Copy Requirements

- Customer copy should avoid security jargon such as token, idempotency, hash, credential, or session internals.
- Preferred concepts: "Scan the current QR", "This item is no longer available", "Review your cart", "Order received".
- Do not offer customer payment, cancellation, discount, refund, or close-session actions in the current release.
