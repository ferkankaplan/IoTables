# TenantApp

## Purpose

TenantApp is the tenant admin interface for a cafe or restaurant created by PlatformApp.

It is served from the tenant subdomain:

```text
https://[tenant].iotables.net
```

The public root page shows basic tenant information. The admin interface is protected behind a separate login route.

TenantApp is used to set up and manage the restaurant operation: halls, tables, stations, menu items, and tenant-level settings.

TenantApp is not the customer ordering interface, station preparation screen, or cashier console. Those flows may use tenant data, but they are separate apps.

When PlatformApp creates a tenant with a sector starter template, TenantApp opens with those starter halls, tables, stations, products, and staff users already created. Starter staff users have bootstrap credentials and must change their password on first login. First-password setup requires OTP sent to the platform-owned tenant identity GSM.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Tenant Admin | Own tenant only | Configure tenant operation, manage halls, tables, stations, and menu items | Cannot access PlatformApp or other tenants |

The first tenant admin is created by PlatformApp during tenant provisioning. The username is the tenant subdomain, the temporary initial password is `admin`, and the user must change the password on first login.

## App Authority

TenantApp can manage tenant-owned setup and configuration records.

| Area | Authority |
| --- | --- |
| Tenant profile | View tenant identity and platform-owned profile fields |
| Hall management | Create, update, organize, and disable halls |
| Table management | Create, update, reorder, and disable tables within halls |
| Station management | Create, update, and disable preparation/service stations |
| Menu management | Create, update, categorize, price, temporarily mark unavailable, and disable products/services and variants/portions |
| Station assignment | Assign products/services to the station responsible for fulfillment |
| Staff management | Manage staff users, roles, and app access |
| Service hall assignment | Assign service staff to the halls they can operate |
| Service delivery tracking | Enable or disable ServiceStaffApp item-delivery tracking for the tenant |
| Starter data editing | Edit or remove sector-based starter records after tenant creation |
| Tenant settings | Manage tenant-scoped operational preferences |

TenantApp must always be tenant-scoped. Every action belongs to the current tenant resolved from the subdomain.

## Not Authorized

- It does not create or suspend tenants.
- It does not change immutable tenant identity fields such as tenant name or tenant subdomain.
- It does not change tenant identity GSM; only PlatformApp can change that number.
- It does not manage platform billing, package limits, or global platform settings.
- It does not directly operate customer table sessions as a cashier.
- It does not prepare station tickets as station staff.
- It does not create customer QR ordering sessions.
- It does not configure fiscal/e-Adisyon/ÖKC integrations in the current release.
- It does not configure kitchen printers, receipt printers, cash drawers, payment terminals, or other hardware integrations in the current release.
- It does not configure waiter-entered orders, package service, courier delivery, pickup, phone orders, marketplace orders, counter sales, stock/recipe, cost accounting, or multi-location operations in the current release.

## UX Principle

TenantApp should use fewer full pages and more contextual panels, drawers, dialogs, and inline editing.

The admin should keep context while working. For example, tables are part of halls and should be managed from the hall management screen. Selecting a table should open a right-side detail panel instead of navigating to a separate table page.

Primary pages should represent stable workspaces. Secondary objects should usually be edited in panels inside those workspaces.

## Screens and URLs

| Screen | URL | Purpose |
| --- | --- | --- |
| Public Tenant Page | `https://[tenant].iotables.net/` | Show basic tenant information without exposing admin controls |
| Tenant Login | `https://[tenant].iotables.net/login` | Authenticate tenant admin |
| Tenant Admin Dashboard | `https://[tenant].iotables.net/admin` | Tenant setup overview and operational readiness |
| Hall Management | `https://[tenant].iotables.net/admin/halls` | Manage halls and their tables in one workspace |
| Station Management | `https://[tenant].iotables.net/admin/stations` | Manage preparation/service stations |
| Menu Management | `https://[tenant].iotables.net/admin/menu` | Manage products, services, variants/portions, pricing, availability, categories, and station assignments |
| Staff Management | `https://[tenant].iotables.net/admin/staff` | Manage staff users, roles, station scopes, and hall scopes |
| Tenant Settings | `https://[tenant].iotables.net/admin/settings` | Manage editable tenant settings |
| Tenant Audit | `https://[tenant].iotables.net/admin/settings?view=audit` | Review tenant setup and security audit in settings context |

Tables may have addressable internal routes for deep linking if needed, but they should not have a primary standalone management page in the first version.

Example implementation option:

```text
https://[tenant].iotables.net/admin/halls?table=:tableId
```

This should open the selected table in a contextual panel inside Hall Management.

## Core Workflows

### Public Tenant Page

1. Visitor opens `https://[tenant].iotables.net/`.
2. TenantApp resolves tenant by subdomain.
3. TenantApp displays basic tenant information.
4. Admin actions are not shown unless the user goes to `/login` and authenticates.

Public Tenant Page visible fields in the current release:

- public display name, falling back to immutable tenant name when no display name exists;
- restaurant sector label when present;
- address when present;
- customer-facing open/available message when later introduced.

The public page must not expose tenant GSM number, platform status internals, staff users, operational health details, table/session state, order data, or setup checklist internals.

### Tenant Admin Login

1. Tenant Admin opens `https://[tenant].iotables.net/login`.
2. TenantApp authenticates against the current tenant.
3. On first login, the temporary `admin` password must trigger password change.
4. After successful password setup, TenantApp opens the admin dashboard.

### Configure Halls and Tables

1. Tenant Admin opens Hall Management.
2. Tenant Admin reviews existing starter halls if a starter template was applied.
3. Tenant Admin creates or edits halls.
4. Tenant Admin selects a hall.
5. TenantApp shows the hall's 100 table slots inside the same workspace.
6. Tenant Admin promotes eligible virtual slots to physical tables, edits, reorders, disables, provisions the table display, or inspects tables from contextual panels.

Tables are part of the hall management context. A table detail should open as a right-side panel, not as a separate primary page.

Current release table layout is an ordered 100-slot grid inside each hall. It does not include visual floor-plan coordinates. Slots `x00` and `x99` are permanent virtual test/system boundary slots and cannot become physical tables. A later floor-plan editor must be introduced as a separate explicit layout capability, not by overloading the current release table order field.

### Configure Service Delivery Tracking

ServiceStaffApp is enabled by default for the initial cafe starter template.

Tenant Admin may disable service delivery tracking for small operations that do not want a separate service queue.

When service delivery tracking is disabled:

- ServiceStaffApp routes should not be shown to staff;
- station `ready` becomes the final fulfillment signal for customer/cashier visibility;
- `picked_up` and `delivered` item tracking is not available;
- the tenant accepts that IoTables will not record who physically delivered the item.

### Configure Tenant Settings

TenantApp may edit these tenant settings in the current release:

- public display name;
- service delivery tracking setting.

TenantApp cannot edit immutable tenant name, tenant subdomain, or tenant identity GSM. Platform-owned profile fields such as GSM, address, capacity, and sector are changed from PlatformApp.

### Configure Stations

1. Tenant Admin opens Station Management.
2. Tenant Admin reviews existing starter stations if a starter template was applied.
3. Tenant Admin creates stations such as kitchen, bar, or service counter.
4. Tenant Admin edits station availability and display details.
5. Station data becomes available for menu item assignment.

### Configure Menu

1. Tenant Admin opens Menu Management.
2. Tenant Admin reviews existing starter products/services if a starter template was applied.
3. Tenant Admin creates categories, products, and services.
4. Tenant Admin sets prices.
5. Tenant Admin assigns each product/service to the station responsible for fulfillment.
6. Disabled products/services remain historical but cannot be ordered.

In v1, each product/service belongs to exactly one fulfillment station. Multi-station routing for the same product is out of the current release unless a later workflow explicitly introduces routing rules.

### Configure Staff and Service Access

1. Tenant Admin opens staff management.
2. Tenant Admin reviews starter staff users if a starter template was applied.
3. Tenant Admin creates staff users with a tenant-unique username and operational display name.
4. TenantApp creates the staff user with default temporary password `12345678`.
5. Tenant Admin assigns app roles such as cashier, station staff, and service staff.
6. Tenant Admin assigns station scopes for station staff and hall scopes for service staff.
7. Staff must change the default password on first login with OTP sent to the platform-owned tenant identity GSM.
8. Tenant Admin disables staff users who should no longer access tenant apps.

### Review Starter Data

1. Tenant Admin logs in after tenant creation.
2. TenantApp shows starter data as normal editable tenant data.
3. Tenant Admin can rename, disable, delete, or extend starter halls, tables, stations, products, and staff users according to normal TenantApp rules.

Starter data must not be recreated automatically after the tenant edits or deletes it.

## Data Concepts Visible in TenantApp

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Summary | Tenant identity resolved from subdomain |
| Tenant identity/profile | Read-only | Tenant identity resolved from subdomain; GSM is platform-owned identity GSM |
| Hall | Full | Tenant-owned physical/operational area |
| Table | Full | Managed inside hall context |
| Station | Full | Fulfillment location for products/services |
| Menu category | Full | Organizes tenant menu |
| Product/service | Full | Menu item/service family |
| Product variant/portion | Full | Orderable unit and current price |
| Availability override | Full | Temporary sold-out/orderability state without disabling catalog history |
| Station assignment | Full | Determines where order items are routed |
| Staff user | Full | Starter users such as cashier, cook, barista, waiter, and busser may be created during provisioning with first-login password change required; waiter and busser are service staff assignments in the current release |
| Service hall assignment | Full | Defines which halls service staff can operate |
| Service delivery tracking setting | Full | Controls whether ServiceStaffApp is active for the tenant |

## Integration Expectations

| Context / Module | Expected Use |
| --- | --- |
| Platform / Tenant Registry | Read tenant identity and platform-owned profile fields. TenantApp does not update identity GSM |
| Access / Identity and Access | Tenant admin authentication and first-login password setup |
| Access / Staff Access | Manage staff roles, station assignments, and hall-based service permissions |
| Tenant Setup / Venue Layout | Manage halls and tables |
| Tenant Setup / Station Setup | Manage fulfillment station definitions |
| Tenant Setup / Menu Catalog | Manage categories, products, services, variants/portions, prices, availability overrides, and station assignments |
| Platform / Sector Starter Templates | Read whether initial tenant data came from a starter template |
| Access / OTP Messaging | Verify password reset flows with OTP sent to tenant identity GSM |
| Governance / Audit | Record tenant admin configuration changes |

## Audit Rules

TenantApp must audit tenant-admin configuration changes that affect access, ordering, fulfillment, or customer-visible identity.

Minimum current release TenantApp audit actions:

- platform-owned tenant identity/profile changes visible to TenantApp;
- public display name changed;
- address, sector, or capacity changed;
- service delivery tracking enabled or disabled;
- hall created, updated, disabled, or reordered;
- table created, updated, disabled, reordered, or display-provisioning state changed;
- station created, updated, or disabled;
- menu category created, updated, disabled, or reordered;
- product/service or variant created, updated, disabled, price-changed, availability override changed, or station assignment changed;
- staff user created, role changed, hall/station scope changed, disabled, or re-enabled.

## Security Rules

- TenantApp resolves tenant context from `[tenant].iotables.net`.
- Tenant users can access only their own tenant.
- Tenant admin routes require authentication.
- Public root page must not expose admin data or operational internals.
- First tenant admin password must be changed on first login.
- First password setup requires OTP sent to the platform-owned tenant identity GSM.
- Tenant name and tenant subdomain are not editable in TenantApp.
- Configuration changes should be audited.
- Starter data is normal tenant-owned data after creation.
- Starter data must not be recreated after Tenant Admin edits, disables, or deletes it.
- Starter staff users must change bootstrap passwords on first login.
- Starter staff first password setup requires OTP sent to the platform-owned tenant identity GSM.
- Service staff must be authorized per hall.
- Service delivery tracking can be disabled only as an explicit tenant setting.
- Fiscal/e-Adisyon/ÖKC, printer, hardware, stock/recipe, package service, courier, pickup, counter sale, and multi-location features are out of the current release scope.

## Open Questions

None currently.
