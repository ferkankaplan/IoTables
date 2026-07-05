# PlatformApp Analytics

PlatformApp analytics defines platform-owner-visible operational measurements. It does not replace audit, tenant health authority, billing authority, or tenant runtime ownership.

Source context:

- [definition.md](definition.md)
- [scenarios.md](scenarios.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [out-of-scope.md](out-of-scope.md)
- [../../modules/platform/tenant-registry.md](../../modules/platform/tenant-registry.md)
- [../../modules/platform/provisioning.md](../../modules/platform/provisioning.md)
- [../../modules/governance/audit.md](../../modules/governance/audit.md)

## Analytics vs Audit

| Concern | PlatformApp Analytics | Audit |
| --- | --- | --- |
| Purpose | Summarize tenant lifecycle, provisioning, DNS readiness, and health trends. | Preserve immutable evidence of sensitive actions. |
| Mutability | Derived and rebuildable. | Append-only. |
| Authority | Never authorizes tenant creation, suspension, recovery, or DNS readiness. | Evidence only; business modules still own decisions. |
| Detail | Aggregated platform-owned metadata. | Actor, action, target, reason, timestamp, safe metadata. |

Platform analytics may reference audit counts, but it must not use audit records as the only source for current tenant state.

## Current Release Metrics

| Metric | Source | Notes |
| --- | --- | --- |
| Active tenant count | Tenant Registry | Count by lifecycle state. |
| Suspended tenant count | Tenant Registry | Include reason category only when safe. |
| Tenant creation attempts | Provisioning + Audit | Created, failed, recoverable. |
| Provisioning failure count | Provisioning | Group by failure stage without leaking secrets. |
| DNS readiness count | Tenant Registry | Manual readiness status only. |
| Starter template applied count | Provisioning | One-time per tenant proof. |
| Tenant health summary count | Tenant Registry health summary | Healthy/degraded/unknown at high level. |
| Platform login/security events count | Audit | Aggregate only. |

## Allowed Surfaces

| Surface | Analytics Behavior |
| --- | --- |
| Platform Dashboard | High-level tenant counts, provisioning status, and health summaries. |
| Tenant List | Sort/filter by lifecycle, DNS readiness, provisioning state, health summary. |
| Tenant Detail | Tenant-scoped lifecycle timeline summary and recovery state. |

PlatformApp analytics must stay inside existing dashboard/list/detail surfaces. It must not create tenant runtime dashboards for orders, payments, stations, table sessions, or customer activity in the current release.

## Data Boundaries

PlatformApp analytics may use:

- tenant identity/profile metadata owned by Platform/Tenant Registry;
- tenant lifecycle and DNS readiness state;
- provisioning attempt state and starter template application state;
- high-level tenant health summaries explicitly exposed to PlatformApp;
- platform-level audit event aggregates.

PlatformApp analytics must not show:

- live tenant orders;
- payment totals;
- table sessions;
- station queues;
- customer sessions or QR tokens;
- staff performance metrics;
- raw health internals that expose tenant runtime data;
- OTP codes, credentials, session tokens, provider payloads, or stack traces.

## Refresh and Consistency

- Analytics cards can be eventually consistent.
- Tenant lifecycle and provisioning action buttons must re-read authoritative module state before mutation.
- Unknown/degraded health is an analytics/display state, not proof that tenant data is invalid.
- If analytics and tenant registry state disagree, Tenant Registry wins.

## Current Release Out of Scope

- Cross-tenant sales reporting.
- Tenant ranking or staff performance dashboards.
- Customer behavior analytics.
- External analytics SaaS export.
- Automated platform decisions based only on analytics.
- Historical data warehouse or arbitrary date-range analytics.

## Acceptance

PlatformApp analytics is acceptable when:

- it summarizes only platform-owned or platform-exposed state;
- it does not expose tenant runtime details;
- it remains separate from immutable audit evidence;
- every displayed metric has an owning module source;
- analytics never becomes authorization or mutation authority.
