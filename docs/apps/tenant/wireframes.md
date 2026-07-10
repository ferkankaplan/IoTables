# TenantApp Wireframes

TenantApp wireframes define the tenant-admin setup workspace and the safe public tenant page. They describe visible workflow and layout responsibility, not React component APIs, CSS, database ownership, or backend contracts.

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

TenantApp lives on the tenant host:

```text
https://[tenant].iotables.net
```

| Surface | URL | UI Shape | Purpose |
| --- | --- | --- | --- |
| Public Tenant Page | `/` | Durable page | Safe public tenant identity. |
| Tenant Login | `/login` | Durable page | Tenant admin login and first password setup. |
| Admin Dashboard | `/admin` | Durable page | Setup readiness overview and starter-data summary. |
| Hall Management | `/admin/halls` | Workspace | Halls and tables in one context. |
| Selected table | `/admin/halls?table=:tableId` | Context panel | Table detail, disable, reorder, display provisioning. |
| Station Management | `/admin/stations` | Workspace | Fulfillment station setup. |
| Menu Management | `/admin/menu` | Workspace | Categories, products/services, variants, modifiers, prices, availability, station assignment. |
| Selected product | `/admin/menu?product=:productId` | Context panel/drawer | Product/service detail without leaving menu context. |
| Staff Management | `/admin/staff` | Workspace | Staff users, roles, station scopes, hall scopes. |
| Tenant Settings | `/admin/settings` | Workspace | Editable profile and operational settings. |
| Tenant Audit | `/admin/settings?view=audit` | Settings view/panel | Tenant setup/security audit without a separate primary page. |

Route query state may select a secondary object. Tenant authority comes from tenant host resolution and Tenant Admin session, not client-supplied IDs alone.

## Public Tenant Page

The public root page shows safe tenant identity only.

Visible fields:

- public display name, falling back to immutable tenant name;
- sector label when present;
- address when present;
- customer-facing open/available message when later introduced.

States:

| State | Behavior |
| --- | --- |
| Loading | Show minimal public shell. |
| Tenant not found | Show unavailable/not-found page. |
| Tenant unavailable | Show safe unavailable state. |
| Public info empty/fallback | Use tenant name fallback; do not expose setup internals. |

No admin controls appear on the public page. Admin access starts only from `/login`.

## Tenant Login

Tenant Login authenticates the Tenant Admin for the current tenant host.

Required states:

| State | Behavior |
| --- | --- |
| Loading | Keep login shell stable. |
| Invalid credentials | Safe rejection without tenant internals. |
| First password change required | Force new password before admin access. |
| Tenant unavailable | Block admin access according to tenant status. |

First-password setup must complete before Admin Dashboard access. OTP is not required for first-password setup in the current release.

## Admin Dashboard

Dashboard summarizes setup readiness and points to the owning workspaces.

```text
+------------------------------------------------+
| Tenant header                          Logout  |
+------------------------------------------------+
| Setup readiness summary                         |
| Starter data / display setup / service mode     |
+------------------------------------------------+
| Halls | Stations | Menu | Staff | Settings      |
+------------------------------------------------+
```

Dashboard states:

| State | Behavior |
| --- | --- |
| Loading | Keep shell/navigation stable. |
| Starter data present | Show starter records as editable tenant data. |
| Setup incomplete | Point to owning workspace; do not auto-create data. |
| Tenant suspended/blocked | Block admin/runtime surfaces according to policy. |

Dashboard must not show live customer orders, payments, table sessions, station queue execution, or cashier controls.

## Hall Management

Hall Management owns halls and tables in one workspace.

```text
+------------------------------------------------+
| Halls                         [Salon ekle]     |
+--------------------+---------------------------+
| Hall list          | Ordered table grid        |
|                    | [Masa] [Masa] [Masa]      |
+--------------------+---------------------------+
|                    | Table detail panel        |
+--------------------+---------------------------+
```

Rules:

- tables are always managed inside hall context;
- current release layout is an ordered grid, not floor-plan coordinates;
- selecting a table opens a contextual panel;
- no standalone primary table management page exists in the current release.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep hall navigation stable. |
| Empty halls | Show create hall action. |
| Selected hall empty tables | Show create table action inside selected hall. |
| Table panel loading | Keep selected hall/table context visible. |
| Table active-session blocked | Disable normal disable/delete; explain recovery requirement. |
| Stale table state | Refresh before destructive/provisioning actions. |

## Table Detail and Display Provisioning

Table Detail Panel contains:

- table name;
- table number and mode (`virtual_test` or `physical`);
- hall assignment/move when allowed;
- display order;
- enabled/disabled state;
- active-session blocker state;
- display provisioning state;
- promote eligible virtual slot to physical action;
- WiFi SSID/password fields for firmware generation on physical tables only;
- generate and download firmware action on physical tables only;
- revoke/rotate display credential actions when available.

Slots ending in `00` or `99` are permanent virtual test/system boundary slots. Their detail panel must not show promote-to-physical or display firmware actions.

Display provisioning states:

| State | Behavior |
| --- | --- |
| Not provisioned | Show WiFi fields and generate firmware action. |
| Firmware generated | Show one-time `masa[no].ino` download with expiry and warning that it will not be shown again. |
| Firmware download expired | Allow new firmware generation; explain that regeneration rotates the credential. |
| Firmware downloaded/provisioned | Show provisioned display state, no raw credential or WiFi password. |
| Re-provisioning | Explain previous credential will be revoked. |
| Revoked | Show no active display credential. |

Raw WiFi passwords and credential secrets must never be shown after their one-time response is dismissed.

## Station Management

Station Management owns station setup only, not preparation queues.

Workspace content:

- station list;
- create station action;
- station detail panel;
- enabled/disabled state;
- disable reason dialog;
- active queue/orderable product blockers.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep station list shell stable. |
| Empty stations | Show create station action before menu items can become orderable. |
| Station disabled | Show disabled state and prevent new routing. |
| Station has active items blocked | Disable normal disable action and explain blocker. |
| Product routes to disabled station | Show menu-routing warning when exposed. |

Station workspace must not expose station staff queue mutation controls.

## Menu Management

Menu Management owns menu setup and customer orderability configuration.

Layout:

```text
+------------------------------------------------+
| Categories                    [Kategori ekle]  |
+--------------------+---------------------------+
| Category list      | Product/service list      |
|                    | Product detail panel      |
+--------------------+---------------------------+
```

Product/service detail supports:

- category;
- station assignment;
- name and description;
- variants/portions;
- prices;
- required/optional modifier groups;
- availability override;
- enabled/disabled state;
- reason-required disable where applicable.

Rules:

- each product/service has exactly one station in the current release;
- product cannot be orderable without an enabled station and valid orderable variant;
- price changes do not rewrite existing order snapshots;
- unavailable means temporary not orderable;
- disabled means preserved for history and not orderable.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep category/product context stable. |
| Empty categories | Show create category action. |
| Empty category products | Show create product/service action. |
| Invalid product | Highlight missing station, variant, price, or modifier rule. |
| Unavailable product | Show not-orderable but editable. |
| Disabled product | Show historical disabled state. |
| Stale station/menu state | Revalidate before save. |

## Staff Management

Staff Management owns staff user setup and app access assignment.

Workspace content:

- staff list;
- create staff drawer;
- staff detail panel;
- role assignment;
- station scopes for station staff;
- hall scopes for service staff;
- disabled user state;
- first-password-required state.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep staff list shell stable. |
| Empty staff | Show create staff user action. |
| Disabled user | Show non-actionable disabled state except allowed re-enable/recovery if later defined. |
| Missing role/scope | Show affected app access warning. |
| Active session permission changed | Show refresh/enforcement notice; backend remains authority. |

Creating a staff user with roles/scopes is one app-level operation. If requested role or scope is invalid, UI must not present a half-created operational staff user as success.

## Tenant Settings

Tenant Settings splits read-only platform-owned profile fields from tenant-owned operational settings.

Read-only from Tenant Registry in TenantApp:

- GSM number;
- address;
- capacity;
- sector classification.

Editable through Tenant Operational Settings:

- public display name;
- service delivery tracking mode.

Immutable:

- tenant name;
- tenant subdomain.

States:

| State | Behavior |
| --- | --- |
| Loading | Keep settings sections stable. |
| Immutable field blocked | Display immutable fields read-only. |
| GSM read-only | Explain identity GSM is changed only from PlatformApp. |
| Service tracking changed | Explain ServiceStaffApp and customer/cashier status impact. |
| Validation error | Field-level error and summary. |
| Stale settings | Refresh before save. |

Service delivery tracking disabled mode must be visually prominent, not hidden as a minor toggle.

## Tenant Audit View

Tenant Audit is a settings view/panel, not a separate primary workspace in the current release.

It shows tenant setup/security audit only:

- platform-owned tenant identity GSM changes as read-only audit events, plus TenantApp-owned public display/address/sector/capacity changes;
- service tracking changes;
- hall/table changes;
- table display provisioning changes;
- station/menu changes;
- staff role/scope/user changes.

It must not show platform-only secrets, raw OTP codes, raw display credentials, customer order contents, cashier payment detail, or station queue runtime detail.

## Responsive Layout

| Viewport | Layout |
| --- | --- |
| Mobile | Single workspace stack; panels become full-height drawers. |
| Tablet | Workspace plus drawer/panel for selected hall/table/product/staff/settings. |
| Desktop | Stable workspaces with right panels and dense but readable lists/grids. |

No layout may depend on viewport-width font scaling. Hall/table labels, product names, station labels, staff roles, and warning text must wrap without overlapping controls.

## Accessibility

- Login, OTP, hall/table/menu/station/staff/settings flows must work by keyboard.
- Drawers and dialogs must trap focus while open and restore focus on close.
- Disable/revoke/service-tracking changes must identify consequence and reason requirement where applicable.
- Ordered table grids need readable row/position labels.
- Status badges must have text, not color alone.
- Touch targets for admin controls must remain usable on mobile fallback.

## Data Visibility Boundaries

TenantApp may show only fields allowed by [visibility.md](visibility.md).

Never show:

- platform billing/package controls;
- tenant lifecycle suspend/reactivate controls;
- live customer carts;
- customer ordering sessions;
- cashier payment controls;
- close-session controls;
- station preparation queue mutation controls;
- service delivery mutation controls;
- raw OTP codes;
- raw display credentials after one-time reveal;
- stack traces or provider payloads.

## Current Release Out-of-Scope UI

The following UI must not appear in TenantApp the current release:

- standalone primary table management page;
- visual floor-plan coordinate editor;
- customer order creation;
- cashier payment, correction, or close-session flows;
- station preparation controls;
- service delivery controls;
- tenant creation/suspension;
- fiscal/e-Adisyon/ÖKC setup;
- printer, cash drawer, payment terminal, or hardware integration setup;
- waiter-entered, package, courier, pickup, phone, marketplace, counter sale, stock/recipe, cost accounting, or multi-location setup.

## Acceptance Check

This wireframe package is valid when:

- every TenantApp scenario has a visible path;
- every state in [ui-states.md](ui-states.md) appears in a surface above;
- tables remain in Hall Management context;
- table display provisioning is table-panel based and one-time-secret safe;
- menu orderability blockers are visible;
- staff role/scope warnings are visible;
- service tracking mode impact is visible;
- no forbidden current release control appears.
