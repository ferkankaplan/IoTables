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

When PlatformApp creates a tenant with a sector starter template, TenantApp opens with those starter halls, tables, stations, products, and staff users already created. Starter staff users have bootstrap credentials and must change their password on first login. The starter cashier must also verify the password setup with OTP SMS. Starter station and service staff do not require OTP in the first version.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Tenant Admin | Own tenant only | Configure tenant operation, manage halls, tables, stations, and menu items | Cannot access PlatformApp or other tenants |

The first tenant admin is created by PlatformApp during tenant provisioning. The username is the tenant subdomain, the temporary initial password is `admin`, and the user must change the password on first login with OTP SMS verification.

## App Authority

TenantApp can manage tenant-owned setup and configuration records.

| Area | Authority |
| --- | --- |
| Tenant profile | View tenant identity and edit allowed tenant fields |
| Hall management | Create, update, organize, and disable halls |
| Table management | Create, update, position, and disable tables within halls |
| Station management | Create, update, and disable preparation/service stations |
| Menu management | Create, update, categorize, price, and disable products/services |
| Station assignment | Assign products/services to the station responsible for fulfillment |
| Staff management | Manage staff users, roles, and app access |
| Service hall assignment | Assign service staff to the halls they can operate |
| Starter data editing | Edit or remove sector-based starter records after tenant creation |
| Tenant settings | Manage tenant-scoped operational preferences |

TenantApp must always be tenant-scoped. Every action belongs to the current tenant resolved from the subdomain.

## Not Authorized

- It does not create or suspend tenants.
- It does not change immutable tenant identity fields such as tenant name or tenant subdomain.
- It does not manage platform billing, package limits, or global platform settings.
- It does not directly operate customer table sessions as a cashier.
- It does not prepare station tickets as station staff.
- It does not create customer QR ordering sessions.

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
| Menu Management | `https://[tenant].iotables.net/admin/menu` | Manage products, services, pricing, categories, and station assignments |
| Tenant Settings | `https://[tenant].iotables.net/admin/settings` | Manage editable tenant settings |

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

### Tenant Admin Login

1. Tenant Admin opens `https://[tenant].iotables.net/login`.
2. TenantApp authenticates against the current tenant.
3. On first login, the temporary `admin` password must trigger password change.
4. Password setup requires OTP SMS verification through the tenant GSM number.
5. After successful login, TenantApp opens the admin dashboard.

### Configure Halls and Tables

1. Tenant Admin opens Hall Management.
2. Tenant Admin reviews existing starter halls if a starter template was applied.
3. Tenant Admin creates or edits halls.
4. Tenant Admin selects a hall.
5. TenantApp shows the hall's tables inside the same workspace.
6. Tenant Admin creates, edits, positions, disables, or inspects tables from contextual panels.

Tables are part of the hall management context. A table detail should open as a right-side panel, not as a separate primary page.

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

### Configure Staff and Service Access

1. Tenant Admin opens staff management.
2. Tenant Admin reviews starter staff users if a starter template was applied.
3. Tenant Admin creates or edits staff users.
4. Tenant Admin assigns roles such as cashier, station staff, waiter, and busser.
5. Tenant Admin assigns service staff to authorized halls.
6. Tenant Admin disables staff users who should no longer access tenant apps.

### Review Starter Data

1. Tenant Admin logs in after tenant creation.
2. TenantApp shows starter data as normal editable tenant data.
3. Tenant Admin can rename, disable, delete, or extend starter halls, tables, stations, products, and staff users according to normal TenantApp rules.

Starter data must not be recreated automatically after the tenant edits or deletes it.

## Data Concepts Visible in TenantApp

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Summary | Tenant identity resolved from subdomain |
| Tenant editable profile | Full | Fields allowed to change after creation |
| Hall | Full | Tenant-owned physical/operational area |
| Table | Full | Managed inside hall context |
| Station | Full | Fulfillment location for products/services |
| Menu category | Full | Organizes tenant menu |
| Product/service | Full | Orderable item or service |
| Station assignment | Full | Determines where order items are routed |
| Staff user | Full | Starter users such as cashier, cook, barista, waiter, and busser may be created during provisioning with first-login password change required |
| Service hall assignment | Full | Defines which halls service staff can operate |

## Integration Expectations

| Future Module | Expected Use |
| --- | --- |
| Tenant Registry | Read tenant identity and editable tenant profile |
| Identity and Access | Tenant admin authentication and first-login password setup |
| Staff Access | Manage staff roles and hall-based service permissions |
| Venue Layout | Manage halls and tables |
| Station Management | Manage fulfillment stations |
| Menu Catalog | Manage categories, products, services, prices, and station assignments |
| Sector Starter Templates | Read whether initial tenant data came from a starter template |
| OTP / Messaging | Verify first password setup with SMS |
| Audit | Record tenant admin configuration changes |

## Security Rules

- TenantApp resolves tenant context from `[tenant].iotables.net`.
- Tenant users can access only their own tenant.
- Tenant admin routes require authentication.
- Public root page must not expose admin data or operational internals.
- First tenant admin password must be changed on first login.
- First password setup requires OTP SMS verification.
- Tenant name and tenant subdomain are not editable in TenantApp.
- Configuration changes should be audited.
- Starter data is normal tenant-owned data after creation.
- Starter data must not be recreated after Tenant Admin edits, disables, or deletes it.
- Starter staff users must change bootstrap passwords on first login.
- Starter cashier first password setup requires OTP SMS verification.
- Starter station and service staff first password setup does not require OTP.
- Service staff must be authorized per hall.

## Open Questions

- Which tenant fields are visible on the public tenant page?
- Which tenant fields are editable in Tenant Settings?
- What exact hall/table layout model will be used?
- Do tables need visual floor-plan positioning in the first version?
- Can one product/service belong to more than one station?
- Which tenant admin actions require audit detail?
