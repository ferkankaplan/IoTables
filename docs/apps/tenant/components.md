# TenantApp Components

This document maps TenantApp UI responsibilities to product-level components. It is not a React API, prop contract, file layout, or visual design system.

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

- Components own tenant-admin setup responsibilities, not runtime execution workflows.
- Components preserve the current workspace while opening secondary object panels/drawers.
- Components must not expose live order/payment/session/preparation/delivery mutation controls.
- Components must show backend-owned blockers and stale states before unsafe setup changes.
- Components must keep public tenant data separate from authenticated admin data.

## Component Map

| Component | Responsibility | Main Sources |
| --- | --- | --- |
| `TenantPublicPage` | Safe public tenant identity. | Tenant context, operational settings public display |
| `TenantLogin` | Tenant admin login, first-password setup, OTP state. | Identity and Access, OTP Messaging |
| `TenantAdminShell` | Protected admin route frame and tenant context. | Session check, tenant profile |
| `SetupDashboard` | Setup readiness, starter data summary, navigation to workspaces. | Tenant profile, starter state, setup APIs |
| `HallWorkspace` | Hall list, selected hall, ordered table grid. | Venue Layout |
| `TableDetailPanel` | Table edit, disable blockers, display provisioning state. | Venue Layout, Table Display Provisioning |
| `DisplayProvisioningPanel` | One-time claim, waiting, provisioned, revoke/rotate states. | Table Display Provisioning |
| `StationWorkspace` | Station list/detail and disable blockers. | Station Setup |
| `MenuWorkspace` | Categories, products/services, variants, modifiers, availability, station routing. | Menu Catalog |
| `ProductDetailPanel` | Product/service setup and orderability validation. | Menu Catalog, Station Setup |
| `StaffWorkspace` | Staff users, roles, station scopes, hall scopes, disabled state. | Staff Access |
| `TenantSettingsWorkspace` | Profile and operational settings. | Tenant Registry, Tenant Operational Settings |
| `TenantAuditPanel` | Tenant setup/security audit records. | Governance Audit |
| `TenantStateMessage` | Loading, empty, stale, blocked, validation, and retry states. | UI states, copy |

## Public and Auth Components

`TenantPublicPage` owns:

- public display name fallback;
- sector label;
- address;
- safe unavailable/not-found states.

It must not show admin actions, tenant GSM, setup state, staff, orders, payments, table sessions, or platform internals.

`TenantLogin` owns:

- login form;
- first-password flow;
- OTP challenge state;
- OTP resend/verify state;
- invalid credentials and tenant unavailable states.

`TenantAdminShell` owns:

- protected admin navigation;
- session check;
- tenant route context;
- logout;
- tenant unavailable/blocked admin state.

## Setup Dashboard

`SetupDashboard` owns setup readiness only.

It may show:

- starter data present;
- halls/stations/menu/staff/settings readiness;
- table display setup summary;
- service tracking mode;
- next workspace links.

It must not create runtime data automatically and must not show live order/payment/session state.

## Hall and Table Components

`HallWorkspace` owns:

- hall list;
- selected hall;
- ordered table grid;
- create/update/disable hall;
- create/update/reorder/disable table entry points.

`TableDetailPanel` owns:

- table name/order/hall assignment;
- enabled/disabled state;
- active TableSession blocker;
- display provisioning entry;
- stale table refresh.

`DisplayProvisioningPanel` owns:

- create claim;
- one-time claim reveal;
- claim expiry;
- waiting for device;
- provisioned display state;
- revoke/rotate credential actions.

Raw claim and credential secrets must be displayed only when the backend returns them and must not be recoverable from normal state reads.

## Station Components

`StationWorkspace` owns:

- station list;
- create/update station;
- disabled state;
- disable reason dialog;
- blockers for active queue and orderable routed products.

It does not own station queue execution. Queue mutation belongs to StationStaffApp.

## Menu Components

`MenuWorkspace` owns:

- category list;
- selected category;
- product/service list;
- product detail panel;
- category create/update/disable;
- product create/update/disable;
- variant and modifier configuration;
- availability override;
- station assignment.

`ProductDetailPanel` must:

- block orderable state without one enabled station;
- block multi-station routing in v1;
- show disabled-station conflicts;
- show invalid variant/modifier/price states;
- keep historical orders safe by disabling instead of hard-deleting when history exists.

Backend remains the authority for customer order validation and price snapshots.

## Staff Components

`StaffWorkspace` owns:

- staff list;
- create staff drawer;
- staff profile panel;
- role assignment;
- station scope assignment;
- hall scope assignment;
- role/scope revoke with reason where required;
- disabled user state;
- first-password-required state.

Staff role/scope UI must be treated as setup visibility. Runtime app access remains enforced server-side on every staff action.

## Settings and Audit Components

`TenantSettingsWorkspace` owns two sections:

| Section | Owner | Editable Fields |
| --- | --- | --- |
| Tenant profile | Tenant Registry | GSM, address, capacity, sector |
| Operational settings | Tenant Operational Settings | public display name, service delivery tracking |

It displays tenant name and subdomain as immutable.

`TenantAuditPanel` owns tenant setup/security audit display inside settings. It must show redacted records only and no runtime order/payment/session detail.

## State Components

Use `TenantStateMessage` for:

- public tenant not found/unavailable;
- invalid login/OTP states;
- empty halls/tables/stations/categories/staff;
- table active-session blockers;
- station active-item/orderable-product blockers;
- product invalid/unavailable/disabled states;
- immutable field blocked;
- service tracking changed;
- staff missing role/scope;
- stale save conflicts.

State messages must use [copy.md](copy.md).

## Data and Action Boundaries

| Boundary | Rule |
| --- | --- |
| Public tenant data | Public-safe only; no admin/runtime internals. |
| Tenant profile | TenantApp edits only allowed mutable fields. |
| Operational settings | TenantApp edits public display name and service tracking. |
| Halls/tables | Managed together in hall context. |
| Table display | One active credential per table; raw secrets one-time only. |
| Stations | Setup only; no queue mutation. |
| Menu | Setup/orderability source; no submitted order mutation. |
| Staff | Roles/scopes setup only; runtime guards remain server-side. |
| Audit | Tenant setup/security audit only. |

## Component Acceptance

The component model is acceptable when:

- every component maps to a wireframe region;
- every component respects TenantApp visibility;
- table detail remains contextual to Hall Management;
- table display provisioning handles one-time secret safety;
- menu/station/staff blockers are represented;
- service tracking setting impact is represented;
- forbidden runtime controls cannot be reached from any component.
