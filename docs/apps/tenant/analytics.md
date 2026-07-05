# TenantApp Analytics

TenantApp analytics defines tenant-admin-visible setup and configuration measurements. It does not replace audit, runtime cashier reporting, station workload, or customer behavior analytics.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/tenant-setup/venue-layout.md](../../modules/tenant-setup/venue-layout.md)
- [../../modules/tenant-setup/station-setup.md](../../modules/tenant-setup/station-setup.md)
- [../../modules/tenant-setup/menu-catalog.md](../../modules/tenant-setup/menu-catalog.md)
- [../../modules/tenant-setup/tenant-operational-settings.md](../../modules/tenant-setup/tenant-operational-settings.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | TenantApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Summarize setup completeness and configuration health. | Preserve immutable evidence of tenant-admin changes. |
| Mutability | Derived and rebuildable from setup state. | Append-only. |
| Authority | Never authorizes setup mutation by itself. | Evidence only. |
| Detail | Counts, completeness, enabled/disabled state. | Actor, action, target, reason, timestamp. |

TenantApp analytics may surface setup warnings, but the owning setup module must still validate every write.

## Current Release Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| Hall count | Venue Layout | Enabled/disabled split. |
| Table count | Venue Layout | Enabled/disabled split and empty setup warning. |
| Station count | Station Setup | Enabled/disabled split. |
| Product count | Menu Catalog | Orderable/unavailable/disabled split. |
| Category count | Menu Catalog | Used for menu organization completeness. |
| Staff user count | Identity/Staff Access | Role counts only; no password/secret data. |
| Station assignment completeness | Menu Catalog + Station Setup | Products without valid station are setup warnings. |
| Service tracking mode | Tenant Operational Settings | Enabled/disabled only. |
| Service hall assignment coverage | Staff Access + Venue Layout | Service staff hall coverage warning. |
| Tenant setup audit count | Audit | Aggregate change activity only. |

## Allowed Surfaces

| Surface | Analytics Behavior |
| --- | --- |
| Admin Dashboard | Setup completeness cards and blocking setup warnings. |
| Hall Management | Hall/table counts and disabled-state warnings. |
| Station Management | Station count and routing warnings. |
| Menu Management | Product/category/orderability counts. |
| Staff Management | Role and assignment coverage counts. |
| Settings/Audit | Audit count summaries beside audit records. |

Analytics should appear inside existing TenantApp workspaces and contextual panels, not as a separate broad reporting product in the current release.

## Data Boundaries

TenantApp analytics may use tenant setup/configuration state:

- halls and tables;
- stations;
- menu categories/products/orderability;
- staff roles and assignments;
- service delivery tracking mode;
- setup audit aggregates.

TenantApp analytics must not show:

- cashier payment totals;
- table-session balances;
- customer ordering funnels;
- station staff performance by actor;
- service staff performance by actor;
- customer session identifiers or QR secrets;
- platform-only tenant lifecycle internals.

## Refresh and Consistency

- Analytics warnings are advisory; write commands must revalidate source state.
- Counts can be eventually consistent.
- If analytics and module state disagree, the setup module state wins.
- Analytics must never unlock unsafe disable/delete actions.

## Current Release Out of Scope

- Revenue/sales analytics.
- Staff performance ranking.
- Customer behavior dashboards.
- Arbitrary historical reporting.
- External BI export.
- Automated tenant setup mutation based on analytics alone.

## Acceptance

TenantApp analytics is acceptable when:

- it summarizes setup completeness without becoming a reporting module;
- it stays inside existing admin workspaces;
- it does not expose runtime payment/order/session detail;
- every metric traces to an owning setup/access module;
- audit remains immutable evidence, not a metrics store.
