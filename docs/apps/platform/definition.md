# PlatformApp

## Purpose

PlatformApp is the private owner interface for operating IoTables as a platform.

It is a single-user admin panel served from `platform.iotables.net`. The first interaction must require login. After login, the platform owner can inspect active tenants, monitor their health, and create new tenants.

PlatformApp authentication uses a platform-scoped Platform Owner account. The first Platform Owner is created by an explicit one-time bootstrap command, not by automatic startup seed logic. V1 PlatformApp login uses username and password only; TOTP is not required for PlatformApp access unless a later security-hardening decision explicitly reintroduces it.

Its main responsibility is to create, inspect, configure, suspend, and support tenant businesses. A tenant represents a cafe or restaurant customer.

PlatformApp is not a tenant runtime interface. It does not operate tables, orders, stations, cashier workflows, customer ordering sessions, or payments directly.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Platform Owner | Global platform scope | Login to PlatformApp, list tenants, inspect tenant health, create tenants, manage platform-level tenant configuration | Does not act as tenant staff by default |

PlatformApp is single-user for the initial product. Additional platform roles, such as support operators, are not part of the first version unless explicitly introduced later.

## App Authority

PlatformApp can manage platform-owned records and platform-level lifecycle decisions.

| Area | Authority |
| --- | --- |
| Tenant registry | Create, view, update, suspend, reactivate |
| Tenant provisioning | Start tenant setup flow |
| Tenant status | Control platform-level availability |
| Tenant domain | Define the immutable tenant subdomain |
| Tenant profile | Define required and optional restaurant metadata |
| Tenant admin bootstrap | Request first tenant admin credentials through Provisioning and Access |
| Tenant starter data | Request sector-based starter data once through Provisioning |
| Tenant health | View high-level tenant health and operational status |
| Tenant limits | Define package, capacity, or feature limits when those concepts exist |
| Platform audit | View platform-level operational history when available |

Tenant name and tenant domain are immutable after creation. Tenant GSM number is required, unique, and editable only by PlatformApp. It is not a normal contact field; it is the tenant identity GSM used for tenant creation OTP and future tenant/staff password reset OTP flows. Optional tenant profile fields can be changed later.

## Not Authorized

PlatformApp must not silently bypass tenant boundaries.

- It does not create customer orders.
- It does not prepare station items.
- It does not close table sessions as a normal cashier flow.
- It does not take payments on behalf of tenant cashiers.
- It does not mutate tenant runtime data unless an explicit support or recovery workflow exists.
- It does not configure fiscal/e-Adisyon/ÖKC integrations in the current release.
- It does not configure external payment providers, printer integrations, hardware terminals, or offline POS mode in the current release.

## Screens and URLs

PlatformApp is served from `platform.iotables.net`.

| Screen | URL | Purpose |
| --- | --- | --- |
| Login | `https://platform.iotables.net/login` | Authenticate the platform owner |
| Platform Dashboard | `https://platform.iotables.net/` | Overview of active tenants and platform health |
| Tenant List | `https://platform.iotables.net/tenants` | List active tenants and their health state |
| Create Tenant | `https://platform.iotables.net/tenants/new` | Create a new tenant business |
| Tenant Detail | `https://platform.iotables.net/tenants/:tenantId` | Inspect tenant profile, domain, status, and setup state |
| Tenant Settings | `https://platform.iotables.net/tenants/:tenantId/settings` | Manage editable platform-owned tenant fields |
| Tenant Audit | `https://platform.iotables.net/tenants/:tenantId/audit` | Review platform-level changes for a tenant |

Tenant runtime apps are served from tenant subdomains:

```text
https://[tenant].iotables.net
```

Tenant subdomains are expected to resolve through the environment wildcard DNS record configured during deployment. PlatformApp does not create, verify, or track per-tenant DNS records.

## Core Workflows

### Login

1. Platform Owner opens `platform.iotables.net`.
2. PlatformApp requires login before showing any tenant data.
3. After successful login, PlatformApp opens the dashboard.

### Create Tenant

1. Platform Owner opens Create Tenant.
2. Platform Owner enters the required tenant identity fields.
3. PlatformApp sends a tenant-creation OTP challenge to the tenant identity GSM.
4. Platform Owner enters the OTP code.
5. PlatformApp validates uniqueness and required platform constraints.
6. Platform Owner may enter optional restaurant metadata.
7. PlatformApp submits the OTP-proven create-tenant command to Provisioning.
6. Provisioning registers the tenant in `provisioning` state through Tenant Registry.
7. Provisioning creates the initial tenant admin and starter staff users through Access.
8. Provisioning applies the selected sector starter template once and creates required tenant setup records.
9. Provisioning activates the tenant only after required records commit.
10. The tenant becomes reachable through the deployed wildcard tenant namespace.

Required fields:

| Field | Required | Mutable After Creation | Notes |
| --- | --- | --- | --- |
| Tenant name | Yes | No | Legal or platform-facing tenant identity |
| Tenant subdomain | Yes | No | Publishes tenant at `https://[tenant].iotables.net` |
| Tenant GSM number | Yes | Yes | Used for OTP SMS during first password setup and future sensitive account flows |

Optional fields:

| Field | Required | Mutable After Creation | Notes |
| --- | --- | --- | --- |
| Restaurant capacity | No | Yes | Capacity definition will be refined later |
| Restaurant sector | No | Yes | Enum. If selected during tenant creation, it determines the one-time starter data template |
| Address | No | Yes | Physical business address |

Tenant name and tenant subdomain are permanent identity fields. If the business needs a different public display name later, that should be modeled as a separate editable field instead of mutating the tenant name.

Changing restaurant sector after tenant creation does not re-run starter data. Sector is an editable profile/classification field after creation, not a provisioning trigger.

### V1 Tenant Scope

PlatformApp creates single-location restaurant tenants in the current release.

Current release tenant creation implies these product boundaries:

- one tenant represents one restaurant/location;
- ordering channel is dine-in table QR only;
- tenant host routing depends on the deployed wildcard DNS namespace;
- CustomerApp cannot take payments;
- CashierApp records operational payments only;
- no fiscal/e-Adisyon/ÖKC integration;
- no external payment provider integration;
- no waiter-entered order channel;
- no pickup, package service, courier, phone order, marketplace order, or counter-sale channel;
- no offline-first local POS mode.

These limits must be visible to the Platform Owner during tenant creation or tenant review so the created tenant is not misrepresented as a full POS/fiscal system.

### Tenant Lifecycle and Health

Current release tenant lifecycle states:

| State | Meaning |
| --- | --- |
| `provisioning` | Tenant creation is running or waiting for completion of initial setup records |
| `active` | Tenant runtime apps may serve normal traffic |
| `suspended` | Tenant runtime apps are intentionally unavailable by platform decision |
| `provisioning_failed` | Tenant creation failed and requires platform recovery or deletion tooling |

New tenants start as `provisioning`. PlatformApp moves the tenant to `active` only after the tenant registry record, first tenant admin, starter data record, and required setup metadata are committed successfully.

DNS is not tenant state. If `*.iotables.net` or the environment-specific wildcard namespace is missing or misconfigured, that is a deployment/ops fault, not a per-tenant checklist item.

The current release does not enforce tenant packages, trials, feature limits, or billing entitlements. Restaurant capacity is informational in the current release unless a later entitlement model explicitly gives it enforcement meaning.

Current release tenant health summary is limited to high-level signals:

- lifecycle state;
- setup/provisioning state;
- starter template applied or failed state;
- tenant admin bootstrap pending or completed state;
- latest platform-visible runtime error summary when available.

Tenant health must not require PlatformApp to inspect or mutate live tenant runtime data such as orders, payments, table sessions, or station queues.

V1 platform support actions are limited to platform-owned control surfaces: inspect tenant metadata, inspect platform audit events, suspend/reactivate tenant, edit tenant GSM number, and retry or inspect failed provisioning through explicit recovery tooling. PlatformApp does not directly rewrite tenant runtime records.

### Apply Sector Starter Data

Starter data is created only during tenant creation. It must never run on server startup, application restart, deployment, migration, or release upgrade.

The provisioning process must record that starter data was applied to the tenant. Once recorded, the same tenant must never receive automatic starter data again unless an explicit, manual recovery tool is built for that purpose.

Initial sector enum:

| Sector | Starter Template |
| --- | --- |
| `cafe` | Cafe starter halls, tables, stations, products, and staff users |

Initial `cafe` starter data:

| Data Type | Created Records |
| --- | --- |
| Halls | `Salon 1`, `Salon 2` |
| Tables per hall | `Masa 000`, `Masa 001`, `Masa 999` |
| Stations | `Mutfak`, `Kahve` |
| Mutfak products | `Sandviç`, `Tost`, `Kurabiye`, `Kek`, `Poğaça` |
| Kahve products | `Kapuçino`, `Americano`, `Türk Kahvesi`, `Çay`, `Latte`, `Espresso` |
| Staff users | `Kasiyer`, `Aşçı`, `Barista`, `Garson`, `Komi` |

Starter data is editable by TenantApp after creation. It is a convenience template, not protected system data.

Starter staff users are created with bootstrap credentials during tenant provisioning. They must change their password on first login.

Initial `cafe` starter staff credentials:

| Staff User | Username | Temporary Password | First Login Requirement |
| --- | --- | --- | --- |
| Kasiyer | `kasiyer` | `admin` | Must change password; OTP not required |
| Aşçı | `asci` | `admin` | Must change password; OTP not required |
| Barista | `barista` | `admin` | Must change password; OTP not required |
| Garson | `garson` | `admin` | Must change password; OTP not required |
| Komi | `komi` | `admin` | Must change password; OTP not required |

These are temporary bootstrap credentials only. They must not allow continued access after the first login without password change.

Cashier first-password setup does not use OTP in the current release. Password reset OTP uses the platform-owned tenant identity GSM.

### Provision Tenant Admin

1. Provisioning creates the first tenant admin through Access during tenant creation.
2. Tenant admin username is the tenant subdomain.
3. Tenant admin initial password is `admin`.
4. Tenant admin must change the password on first login.

The initial `admin` password is a temporary bootstrap credential only. It must not allow continued access after first login without password change.

### List Active Tenants

1. Platform Owner opens the dashboard or Tenant List.
2. PlatformApp lists active tenants.
3. Each tenant row shows identity, domain, status, and health summary.
4. Platform Owner can open Tenant Detail for deeper inspection.

### Suspend Tenant

1. Platform Owner opens Tenant Detail.
2. Platform Owner chooses suspend.
3. PlatformApp requires a reason.
4. Tenant becomes unavailable according to the suspension policy.
5. Tenant-facing apps must respect the suspended state.

### Inspect Tenant

1. Platform Owner opens Tenant Detail.
2. PlatformApp displays platform-owned tenant identity, lifecycle state, and setup status.
3. Tenant runtime details may be summarized, but mutation must go through explicit support flows.

## Data Concepts Visible in PlatformApp

PlatformApp may display these concepts, but it does not necessarily own all future domain details.

| Concept | Visibility | Notes |
| --- | --- | --- |
| Tenant | Full | Primary platform object |
| Tenant name | Full | Required and immutable |
| Tenant subdomain | Full | Required and immutable |
| Tenant GSM number | Full | Required, unique, editable only by PlatformApp, platform-owned identity GSM |
| Tenant address | Full | Optional and editable |
| Tenant sector | Full | Optional and editable |
| Tenant capacity | Full | Optional and editable |
| Tenant status | Full | Platform lifecycle state |
| Tenant health | Summary | High-level operational state shown in lists and detail screens |
| Tenant setup state | Full | Tracks readiness/provisioning |
| Tenant starter data state | Full | Records whether one-time starter data was applied |
| Tenant owner/admin | Partial | Created during tenant provisioning; username is tenant subdomain |
| Tenant limits/features | Full | Future package and entitlement model |
| Tenant audit events | Full | Platform-level audit only |

## Integration Expectations

PlatformApp interacts with domain modules through explicit interfaces.

| Context / Module | Expected Use |
| --- | --- |
| Platform / Provisioning | Start tenant creation, inspect provisioning state, retry explicit recovery |
| Platform / Tenant Registry | Manage tenant identity, lifecycle, profile, subdomain, GSM, and tenant health summary |
| Platform / Sector Starter Templates | List sector options and record one-time starter application through Provisioning |
| Access / Identity and Access | Create platform owner, tenant admin, and starter staff accounts through controlled bootstrap flows |
| Access / OTP Messaging | Support tenant creation and future password reset OTP flows |
| Governance / Audit | Record platform-level actions |

DNS automation is not part of PlatformApp for the initial product. Tenant host routing is provided by wildcard DNS configured at the environment/deployment layer.

SMS provider selection is not a PlatformApp product decision. PlatformApp depends on the OTP / Messaging contract; the concrete SMS provider should be selected later behind that adapter.

## Security Rules

- PlatformApp is private and must require platform-owner authentication.
- PlatformApp is single-user in the first version.
- Platform Owner is a platform-scoped user, not a tenant user.
- Platform Owner login requires username/password only in the current release.
- Platform Owner bootstrap must be explicit and one-time; it must not run on application restart or deployment.
- Tenant users must never access PlatformApp.
- Platform actions must be audited.
- Destructive actions require explicit confirmation.
- Support access to tenant runtime data must be intentional, visible, and permissioned.
- Tenant name and tenant subdomain cannot be edited after creation.
- Tenant GSM number is unique, owned by PlatformApp, editable only through PlatformApp, and every change must be audited.
- Tenant creation requires OTP verification against the requested tenant GSM number before provisioning starts.
- Initial tenant admin password is temporary and must be changed on first login.
- Starter staff passwords are temporary and must be changed on first login.
- Starter tenant admin and cashier first password setup does not require OTP in the current release.
- Staff password reset OTP is sent to the platform-owned tenant identity GSM number.
- Starter station and service staff password setup does not require OTP unless their role is later expanded with critical financial or administrative authority.
- Sector starter data must be applied only once during tenant creation.
- Sector starter data must not run during server startup, restart, deployment, migration, or release upgrade.
- Changing tenant sector after creation must not re-run starter data.

## Open Questions

None currently.
