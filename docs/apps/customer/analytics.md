# CustomerApp Analytics

CustomerApp analytics defines anonymous product/UX measurement for the customer ordering flow. CustomerApp does not show analytics UI to customers in the current release.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/ordering/table-presence.md](../../modules/ordering/table-presence.md)
- [../../modules/ordering/customer-ordering.md](../../modules/ordering/customer-ordering.md)
- [../../modules/settlement/table-session-billing.md](../../modules/settlement/table-session-billing.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | CustomerApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Improve QR, menu, cart, and order UX through anonymous funnel signals. | Preserve evidence of accepted orders and sensitive actions. |
| Mutability | Derived, aggregate, disposable. | Append-only. |
| Authority | Never proves table presence or authorizes ordering. | Evidence only. |
| Detail | Anonymous event counts and timings. | Structured business action records. |

Fresh QR presence and order submission authority come from Table Presence and Customer Ordering, not analytics.

## Current Release Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| QR redemption attempts | Table Presence | Aggregate success/expired/consumed counts only. |
| Fresh presence expiry rate | Table Presence | No raw QR token or customer identity. |
| Menu load success/failure | CustomerApp/API responses | Aggregate by tenant/table only when safe. |
| Cart add/remove count | CustomerOrderingSession | Anonymous session-level aggregate. |
| Submit order attempts | Customer Ordering | Submitted/rejected/idempotent replay counts. |
| Order submission latency | Customer Ordering/API | Operational UX metric. |
| Cart validation rejection count | Customer Ordering/Menu Catalog | Group by safe reason category. |
| Table orders view usage | CustomerApp | Aggregate read behavior only. |
| Bill summary view usage | Settlement/Payments read | Aggregate read behavior only. |

## Allowed Surfaces

CustomerApp current release has no customer-visible analytics screen.

Analytics may be emitted internally from existing surfaces:

- QR redemption;
- menu browsing;
- cart editing;
- order submission;
- order status view;
- table orders view;
- bill summary view.

## Data Boundaries

CustomerApp analytics may use:

- anonymous CustomerOrderingSession identifier only as an internal aggregation key;
- table/session context after authorized QR redemption;
- safe reason categories for rejected order attempts;
- timing and count values.

CustomerApp analytics must not store or expose:

- raw QR tokens;
- display credentials;
- OTP/session cookies;
- customer personal identity;
- precise device fingerprinting;
- cashier-only correction data;
- payment mutation data;
- stack traces or internal exception details.

## Refresh and Consistency

- Analytics failure must never block menu browsing, cart preservation, order submission, or status display.
- Analytics events are best-effort unless later operational requirements define a durable telemetry pipeline.
- Order idempotency and presence freshness must be enforced without analytics.
- If analytics and source records disagree, source records win.

## Current Release Out of Scope

- Customer-visible analytics dashboards.
- Personalized recommendations.
- Cross-tenant customer tracking.
- Marketing attribution.
- External advertising pixels.
- Customer payment conversion analytics, because customer payment is out of the current release.

## Acceptance

CustomerApp analytics is acceptable when:

- it is anonymous and aggregate by default;
- it never becomes QR, order, session, or payment authority;
- it does not affect customer UX when telemetry fails;
- every metric traces to CustomerApp scenario events or owning module reads;
- audit remains reserved for accepted business actions and sensitive evidence.
