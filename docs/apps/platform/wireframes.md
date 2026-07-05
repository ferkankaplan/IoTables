# PlatformApp Wireframes

PlatformApp wireframes define the private platform-owner workspace for tenant creation, tenant lifecycle, setup health, and platform-safe support visibility. They describe product workflow and layout responsibility, not React component APIs, CSS tokens, database ownership, or backend contracts.

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

## Route and Workspace Decisions

PlatformApp lives on the platform host:

```text
https://platform.iotables.net
```

PlatformApp uses a small set of durable routes. Secondary records open as contextual panels or drawers where this preserves the tenant list context.

| Surface | URL | UI Shape | Purpose |
| --- | --- | --- | --- |
| Login | `/login` | Durable page | Platform Owner username/password authentication. |
| Dashboard | `/` | Durable page | Platform health and tenant status overview. |
| Tenant Workspace | `/tenants` | Durable page | Tenant list, filters, health, selected tenant detail panel. |
| Create Tenant | `/tenants/new` | Drawer route | Tenant creation form and provisioning result without leaving tenant workspace. |
| Tenant Detail | `/tenants/:tenantId` | Detail panel route | Profile, lifecycle, DNS, provisioning, starter, and health summary. |
| Tenant Settings | `/tenants/:tenantId/settings` | Detail panel tab/route | Editable platform-owned tenant fields. |
| Tenant Audit | `/tenants/:tenantId/audit` | Detail panel tab/route | Platform-level audit and lifecycle timeline. |

The route may select a tenant or drawer state, but tenant authority comes from Platform Owner session and backend Platform/Tenant Registry APIs.

## Login Surface

Login is the only public PlatformApp surface. No tenant data appears before authenticated Platform Owner access.

Required states:

| State | Wireframe Behavior |
| --- | --- |
| Loading | Show minimal login shell while login requirements/session state loads. |
| Bootstrap user missing | Show setup unavailable state; no dashboard link. |
| First password change required | Force password change before dashboard access. |
| Invalid credentials | Show safe failure without exposing tenant data or account existence details. |
| Platform user disabled | Reject access and keep tenant data hidden. |

Login and required setup flows use dialogs/steps inside the login surface. Dashboard access appears only after backend authentication and required setup completion.

## Dashboard

Dashboard gives a compact platform overview, not tenant runtime control.

```text
+------------------------------------------------+
| Platform header                   Logout       |
+------------------------------------------------+
| Health summary: active / failed / suspended    |
| DNS not ready / provisioning failed / unknown  |
+------------------------------------------------+
| Tenant health list preview                     |
| [Tenant row] [Tenant row] [Tenant row]         |
+------------------------------------------------+
```

Dashboard regions:

| Region | Component Responsibility |
| --- | --- |
| Header/session | `PlatformShell` |
| Health counters | `PlatformHealthSummary` |
| Tenant preview | `TenantHealthList` |
| Critical failures | `ProvisioningStatePanel` summary links |

Dashboard must not expose live order, payment, station, table-session, cart, or preparation data.

## Tenant Workspace

Tenant Workspace is the primary PlatformApp workspace.

```text
+------------------------------------------------+
| Platform header                                |
| [Tenant oluştur]                               |
+------------------------------------------------+
| Filters: status / sector / search             |
+-------------------------+----------------------+
| Tenant health list      | Selected tenant      |
|                         | detail panel         |
|                         |                      |
+-------------------------+----------------------+
```

Tenant list row fields:

| Field | Notes |
| --- | --- |
| Tenant name | Immutable platform identity. |
| Subdomain | Immutable tenant domain. |
| Status | `provisioning`, `active`, `suspended`, `provisioning_failed`. |
| DNS readiness | Manual checklist status. |
| Sector | Optional classification. |
| Provisioning state | Setup/starter/admin bootstrap summary. |
| Health flags | High-level safe platform health only. |

Tenant list states:

| State | Behavior |
| --- | --- |
| Loading | Keep filters/header stable; show list skeleton. |
| Empty tenant list | Show create tenant action. |
| Partial health unavailable | Show unknown/degraded health without hiding identity metadata. |
| Tenant row stale | Disable lifecycle/DNS actions until refresh. |
| Platform auth expired | Redirect to login and do not keep tenant data visible. |

## Create Tenant Drawer

Create Tenant opens as a drawer from Tenant Workspace. `/tenants/new` may be loaded directly and should open the same drawer route.

Required fields:

- tenant name;
- tenant subdomain;
- tenant GSM number.

Optional fields:

- restaurant sector enum;
- restaurant capacity;
- address.

The sector field shows supported enum options. Selecting `cafe` may show a starter template preview, but the UI must state that starter data applies only once during tenant creation.

Create Tenant states:

| State | Behavior |
| --- | --- |
| Pristine | Required fields marked; submit disabled until minimally valid. |
| Validating | Field-level validation without leaving drawer. |
| Subdomain duplicate | Mark subdomain field and block submit. |
| Submitting | Disable submit and form mutation; keep entered values visible. |
| Duplicate submit replay | Show original provisioning result; do not create a parallel tenant. |
| Provisioning | Show reserved tenant identity and setup progress. |
| Provisioning failed | Show redacted safe failure and recovery affordance when available. |
| Success | Show tenant identity, subdomain, status, starter state, admin bootstrap state, and DNS checklist. |

Create Tenant must not claim DNS is created automatically. It must show manual DNS as a post-creation checklist item.

## Tenant Detail Panel

Tenant Detail opens from a tenant row and keeps the list context visible on tablet/desktop. On mobile it may become a full-height drawer.

Detail sections:

- identity: name, subdomain, created time;
- editable profile: GSM, sector, capacity, address;
- lifecycle: current status, last status event, suspend/reactivate action;
- DNS readiness: manual flag and last update;
- provisioning: setup state, failed phase, recovery summary;
- starter data: selected template, version, applied/failed state;
- tenant admin bootstrap: pending/completed summary;
- platform-safe health flags;
- platform audit/lifecycle event link.

Detail states:

| State | Behavior |
| --- | --- |
| Loading | Keep selected row highlighted and panel skeleton stable. |
| Not found/hidden | Show safe not-found state and keep list available. |
| Suspended | Show suspended badge, reason where allowed, and reactivate action. |
| Provisioning | Show setup progress and block normal lifecycle shortcuts. |
| Provisioning failed | Show failure state and recovery action if allowed. |
| DNS not ready | Show checklist warning, not runtime mutation. |
| Health unavailable | Show unknown/degraded summary without blocking profile edits. |
| Stale detail | Refresh before allowing lifecycle, DNS, or retry actions. |

## Tenant Settings

Settings is a tab or panel route inside Tenant Detail.

Editable fields:

- GSM number;
- sector;
- capacity;
- address.

Immutable fields:

- tenant name;
- tenant subdomain.

Rules:

- Immutable fields may be displayed but not edited.
- GSM update is sensitive and must show audited-change copy.
- Changing sector after creation must not re-run starter data.
- Profile save must show pending, validation error, stale, and success states.

## Tenant Audit

Tenant Audit is a tab or panel route inside Tenant Detail.

It shows platform-level events only:

- tenant creation;
- provisioning state changes;
- starter template applied/failed/recovery-needed;
- DNS readiness changes;
- lifecycle changes;
- GSM updates;
- platform support/recovery actions when available.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep selected tenant context visible. |
| Empty audit | Show no platform-level audit events. |
| Filtered empty | Show no events match filters. |
| Access denied | Hide event details and show safe authorization state. |

Audit must not show raw OTP, secrets, provider payloads, runtime order/payment detail, or stack traces.

## Lifecycle and DNS Actions

Sensitive actions use explicit dialogs.

| Action | UI Shape | Required Behavior |
| --- | --- | --- |
| Suspend tenant | Dialog | Reason required; pending disables confirm. |
| Reactivate tenant | Dialog | Reason required; stale state refresh before confirm. |
| Mark DNS ready/not ready | Confirmation or inline guarded control | Manual checklist copy; no DNS automation claim. |
| Retry failed provisioning | Recovery drawer/dialog | Shows safe summary; does not rerun completed starter data. |
| Update GSM | Settings save with sensitive-change message | Audit expectation visible. |

Success state appears only after backend acceptance.

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Basic admin fallback; tenant list remains readable; detail/create panels become full-height drawers. |
| Tablet | Tenant list plus drawer/panel; filters stay compact; actions remain reachable. |
| Desktop | Tenant health table/list with persistent detail/recovery panel. |

No layout may depend on viewport-width font scaling. Tenant names, domains, failure summaries, and action copy must wrap inside stable containers without overlapping controls.

## Accessibility

- Login, tenant creation, lifecycle dialogs, DNS control, and provisioning retry must work by keyboard.
- Drawers and dialogs must trap focus while open and restore focus on close.
- Status badges require accessible text, not color alone.
- Destructive/sensitive dialogs must identify the tenant and action consequence.
- Tables/lists must support readable row focus and selected-row state.

## Data Visibility Boundaries

PlatformApp may show only platform-safe state from [visibility.md](visibility.md).

Never show:

- customer cart contents;
- CustomerOrderingSession data;
- live table-session operational detail;
- live station queue detail;
- cashier payment mutation data;
- raw OTP/SMS provider payloads;
- raw secrets, credentials, tokens, hashes, stack traces, or internal paths;
- tenant runtime mutation controls for orders, preparation, delivery, payments, or sessions.

## Current Release Out-of-Scope UI

The following UI must not appear in PlatformApp the current release:

- create customer order;
- prepare station item;
- deliver item;
- close table session as cashier;
- receive or void payment as cashier;
- mutate live tenant runtime orders, payments, sessions, preparation, delivery, carts, or station queues;
- DNS record automation;
- fiscal/e-Adisyon/ÖKC setup;
- external payment provider setup;
- printer, terminal, cash drawer, or offline POS setup;
- package/courier/phone/marketplace/counter-sale channel setup.

## Acceptance Check

This wireframe package is valid when:

- every PlatformApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- tenant creation shows required fields, idempotent pending/replay behavior, provisioning result, and DNS checklist;
- lifecycle and sensitive profile actions require backend acceptance before success;
- platform health stays high-level and does not become tenant runtime control;
- no forbidden current release control appears.
