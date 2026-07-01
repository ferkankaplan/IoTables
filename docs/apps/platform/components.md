# PlatformApp Components

This document maps PlatformApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

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

- Components own Platform Owner workflow responsibilities, not tenant runtime entities.
- Components may show high-level health summaries, but they must not expose or mutate tenant runtime orders, payments, sessions, carts, preparation, or delivery state.
- Components preserve tenant list context while opening creation, detail, settings, audit, and recovery surfaces.
- Components must show pending, stale, blocked, and failure states for mutating actions.
- Components must not provide DNS automation or starter-data rerun controls in v1.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `PlatformShell` | Platform route frame, authenticated session state, logout, app navigation. | Session check |
| `PlatformLogin` | Login, first-password, TOTP enrollment/verification, and blocked setup states. | Identity and Access |
| `PlatformHealthSummary` | High-level tenant lifecycle/setup/health counters. | Tenant health list |
| `TenantHealthList` | Tenant list with filters, lifecycle, DNS, provisioning, starter, and health flags. | Tenant Registry |
| `TenantCreateDrawer` | Tenant creation form, sector template preview, idempotent submit, provisioning result. | Provisioning, Sector Starter Templates |
| `TenantDetailPanel` | Selected tenant profile, lifecycle, setup, DNS, starter, admin bootstrap, and safe health summary. | Tenant Registry, Provisioning |
| `TenantSettingsPanel` | Editable platform-owned tenant profile fields. | Tenant Registry |
| `TenantAuditPanel` | Platform audit/lifecycle timeline for selected tenant. | Audit, Tenant Registry |
| `ProvisioningStatePanel` | Provisioning progress, failed state, recovery summary, retry action. | Provisioning |
| `DnsReadinessControl` | Manual DNS readiness flag and audit-visible state. | Tenant Registry |
| `TenantLifecycleDialog` | Suspend/reactivate confirmation with reason. | Tenant Registry |
| `PlatformStateMessage` | Loading, empty, unauthorized, stale, blocked, and retry states. | UI states, copy |

## Shell and Access Components

`PlatformShell` owns:

- platform host app frame;
- authenticated session check;
- protected route gate;
- logout action;
- top-level navigation to dashboard and tenant workspace.

`PlatformLogin` owns:

- username/password login;
- login requirements state;
- first password change requirement;
- TOTP enrollment requirement;
- TOTP verification requirement;
- invalid credential/TOTP messages;
- bootstrap-user-missing blocked state.

`PlatformLogin` must not show tenant list, health, audit, tenant names, or tenant count before successful Platform Owner authentication.

## Tenant List Components

`PlatformHealthSummary` summarizes:

- active tenant count;
- suspended tenant count;
- provisioning tenant count;
- provisioning failed count;
- DNS not ready count;
- health unknown/degraded count.

`TenantHealthList` owns:

- tenant filters by status, sector, and search;
- cursor/pagination controls;
- selected-row state;
- lifecycle/status badges;
- DNS readiness indicator;
- safe high-level health flags;
- empty and partial-health states.

It does not own tenant runtime drill-downs.

## Tenant Creation Components

`TenantCreateDrawer` owns:

- required tenant name, subdomain, and GSM fields;
- optional sector, capacity, and address fields;
- sector options loading;
- starter template preview;
- v1 scope notice;
- create submit state;
- idempotent replay result;
- provisioning result summary;
- DNS manual checklist prompt after creation.

Validation responsibilities:

- block submit when required fields are missing;
- show duplicate subdomain field error;
- preserve form data on validation failure;
- disable form mutation while create submit is pending;
- show safe provisioning failure and recovery link when available.

Backend remains responsible for final authorization, uniqueness, idempotency, provisioning transaction, starter application uniqueness, and audit.

## Tenant Detail Components

`TenantDetailPanel` owns selected tenant context:

- immutable identity display;
- lifecycle state;
- DNS readiness;
- provisioning state;
- starter application state;
- tenant admin bootstrap summary;
- high-level health flags;
- navigation to settings/audit tabs;
- stale state refresh before sensitive actions.

`TenantSettingsPanel` owns editable platform profile fields:

- GSM number;
- sector;
- capacity;
- address.

It displays tenant name and subdomain as immutable. It must state that sector changes after creation do not re-run starter data.

`TenantAuditPanel` owns platform-level audit and lifecycle event display. It must not show runtime order/payment/session details, raw secrets, stack traces, or provider payloads.

## Provisioning and Recovery Components

`ProvisioningStatePanel` owns:

- provisioning status;
- starter application status;
- failed phase if exposed safely;
- redacted failure summary;
- DNS checklist state;
- recovery summary;
- retry action for allowed failed provisioning.

Retry behavior:

- retry is not the same as create tenant submit;
- retry must not re-run completed starter data;
- pending retry disables retry action;
- stale state requires refresh before retry;
- success updates detail/list state only after backend acceptance.

## DNS and Lifecycle Components

`DnsReadinessControl` owns:

- manual ready/not-ready flag;
- clear manual-DNS copy;
- pending state;
- audited update expectation.

It must not provide DNS provider credentials, DNS record creation, DNS verification automation, or automatic subdomain management in v1.

`TenantLifecycleDialog` owns:

- suspend confirmation;
- reactivate confirmation;
- reason field;
- stale state recovery;
- pending state;
- backend failure state.

Lifecycle actions must not be available when the selected tenant state is stale or the transition is invalid.

## State Components

Use `PlatformStateMessage` for:

- login loading;
- bootstrap unavailable;
- invalid credentials/TOTP;
- empty tenant list;
- tenant not found/hidden;
- partial health unavailable;
- tenant row/detail stale;
- provisioning failed;
- DNS not ready;
- access denied;
- audit empty/filtered empty.

State messages must use [copy.md](copy.md) and remain platform-safe.

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Tenant identity | PlatformApp can display and create; name/subdomain immutable after creation. |
| Tenant GSM | PlatformApp can edit; changes are audited and affect future OTP flows. |
| Sector | PlatformApp can select/edit classification; starter data applies only during tenant creation. |
| Starter data | PlatformApp can request through Provisioning and view application state; cannot rerun by profile edit. |
| DNS | PlatformApp can track manual readiness only. |
| Tenant health | High-level safe summary only. |
| Runtime tenant data | No normal PlatformApp mutation or detail drill-down. |
| Audit | Platform-level/redacted events only. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects PlatformApp visibility;
- login/setup gates hide tenant data until Platform Owner access is valid;
- tenant creation has pending, duplicate replay, failure, and success representation;
- provisioning recovery does not duplicate create-tenant behavior;
- DNS readiness is manual-only;
- lifecycle actions require reason and backend acceptance;
- forbidden v1 runtime controls cannot be reached from any component.
