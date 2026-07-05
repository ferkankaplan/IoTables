# ServiceStaffApp Analytics

ServiceStaffApp analytics defines service delivery workload measurements visible to service staff when service tracking is enabled. It does not replace delivery state, audit, cashier settlement, or hall authorization.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/fulfillment/service-delivery.md](../../modules/fulfillment/service-delivery.md)
- [../../modules/fulfillment/preparation.md](../../modules/fulfillment/preparation.md)
- [../../modules/access/staff-access.md](../../modules/access/staff-access.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | ServiceStaffApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Summarize ready/picked-up/delivered workload and delivery timing. | Preserve delivery transition evidence. |
| Mutability | Derived/rebuildable from Preparation and DeliveryState. | Append-only. |
| Authority | Never authorizes hall scope or delivery transitions. | Evidence only. |
| Detail | Counts, age, duration, same-day delivery activity. | Actor/action/target/timestamp. |

Service tracking disabled means ServiceStaffApp has no active delivery analytics surface in the current release.

## Current Release Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| Ready item count | Preparation + Service Delivery | Authorized hall scope only. |
| Picked-up item count | Service Delivery | Authorized hall scope only. |
| Oldest ready age | Preparation | Time since ready. |
| Delivered count today | Service Delivery | Same-day count. |
| Average ready-to-delivered time | Preparation + Service Delivery | Show only when enough data exists. |
| Bulk delivery count | Service Delivery | Aggregate same-table bulk use. |
| Recent delivery count | Service Delivery recent deliveries | Same-day recent view. |

## Allowed Surfaces

| Surface | Analytics Behavior |
| --- | --- |
| Service Queue | Workload bar and table-group counts. |
| Item Detail | Ready age and delivery timing context. |
| Bulk Delivery | Selected count and same-table validation summary. |
| Recent Deliveries | Same-day delivered/recent activity. |

Analytics must not appear when service tracking is disabled, except for a non-actionable disabled state.

## Data Boundaries

ServiceStaffApp analytics may use:

- readiness timestamps from Preparation;
- picked-up/delivered state from Service Delivery;
- authorized hall scope;
- same-day recent delivery activity.

ServiceStaffApp analytics must not show:

- payment totals or balances;
- cashier corrections;
- tenant setup mutation controls;
- station preparation mutation controls;
- customer session/cart data;
- delivery items outside authorized halls.

## Refresh and Consistency

- Metrics can be eventually consistent.
- Pickup/deliver actions must re-read authoritative item state before mutation.
- If analytics and queue state disagree, Service Delivery/Preparation state wins.
- Metrics must refresh after single-item or bulk delivery actions.

## Current Release Out of Scope

- Staff performance ranking.
- Payroll/productivity reports.
- Customer satisfaction analytics.
- Cross-tenant delivery comparison.
- Historical arbitrary date-range reports.

## Acceptance

ServiceStaffApp analytics is acceptable when:

- metrics are shown only for authorized halls and enabled service tracking;
- metrics are derived from Preparation and Service Delivery;
- analytics never authorizes delivery mutation;
- audit remains the transition evidence source;
- forbidden payment/setup/customer data is absent.
