# StationStaffApp Analytics

StationStaffApp analytics defines station workload measurements visible to station staff and later operational review. It does not replace preparation state, audit, cashier correction, or staff authorization.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/fulfillment/preparation.md](../../modules/fulfillment/preparation.md)
- [../../modules/access/staff-access.md](../../modules/access/staff-access.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | StationStaffApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Summarize current station workload and preparation timing. | Preserve transition evidence. |
| Mutability | Derived/rebuildable from preparation records. | Append-only. |
| Authority | Never authorizes station access or status transitions. | Evidence only. |
| Detail | Counts, age, duration, current-day recent activity. | Actor/action/target/timestamp/reason. |

Station queue state and transitions remain owned by Preparation.

## Current Release Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| Pending item count | Preparation | Authorized station scope only. |
| Preparing item count | Preparation | Authorized station scope only. |
| Ready waiting item count | Preparation | Authorized station scope only. |
| Oldest waiting age | Preparation | From ordered/preparation timestamps. |
| Average preparation time | Preparation transitions | Show only when enough data exists. |
| Cannot-prepare count | Preparation | Current business-day count. |
| Recent completed count | Preparation recent items | Same-day recent view. |

## Allowed Surfaces

| Surface | Analytics Behavior |
| --- | --- |
| Station Selector | Show authorized station workload counts. |
| Station Queue | Workload bar, oldest age, and status counts. |
| Item Detail | Item timing context only. |
| Recent Items | Same-day completed/cannot-prepare activity. |

Analytics must stay inside the station workflow. It must not become a tenant admin reporting dashboard in StationStaffApp.

## Data Boundaries

StationStaffApp analytics may use:

- preparation item status and timestamps;
- authorized station scope;
- same-day recent preparation activity;
- safe cannot-prepare reason counts when visible.

StationStaffApp analytics must not show:

- payment totals or balances;
- cashier corrections;
- service delivery mutation controls;
- customer session/cart data;
- tenant setup mutation controls;
- cross-station data outside staff authorization.

## Refresh and Consistency

- Metrics can be eventually consistent.
- Transition buttons must re-read authoritative item state before mutation.
- If metrics and queue state disagree, Preparation queue state wins.
- Metrics must refresh after start/ready/cannot-prepare actions.

## Current Release Out of Scope

- Staff performance ranking.
- Payroll/productivity reports.
- Cost/recipe/stock analytics.
- Cross-tenant station comparison.
- Historical arbitrary date-range reports.

## Acceptance

StationStaffApp analytics is acceptable when:

- metrics match the authorized station scope;
- metrics are derived from Preparation, not independent state;
- analytics never authorizes transitions;
- audit remains the transition evidence source;
- forbidden financial/setup/customer data is absent.
