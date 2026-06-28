# PlatformApp

## Purpose

PlatformApp is the private owner interface for operating IoTables as a platform.

It is used only by the platform owner. Its main responsibility is to create, inspect, configure, suspend, and support tenant businesses. A tenant represents a cafe or restaurant customer.

PlatformApp is not a tenant runtime interface. It does not operate tables, orders, stations, cashier workflows, customer ordering sessions, or payments directly.

## Users and Access

| User | Scope | Allowed Capabilities | Limits |
| --- | --- | --- | --- |
| Platform Owner | Global platform scope | Manage tenants and platform-level configuration | Does not act as tenant staff by default |
| Support Operator | Optional future role | Inspect tenant state and assist with operational issues | Cannot perform destructive or financial actions without explicit permission |

## App Authority

PlatformApp can manage platform-owned records and platform-level lifecycle decisions.

| Area | Authority |
| --- | --- |
| Tenant registry | Create, view, update, suspend, reactivate |
| Tenant provisioning | Start tenant setup flow |
| Tenant status | Control platform-level availability |
| Tenant limits | Define package, capacity, or feature limits when those concepts exist |
| Platform audit | View platform-level operational history when available |

## Not Authorized

PlatformApp must not silently bypass tenant boundaries.

- It does not create customer orders.
- It does not prepare station items.
- It does not close table sessions as a normal cashier flow.
- It does not take payments on behalf of tenant cashiers.
- It does not mutate tenant runtime data unless an explicit support or recovery workflow exists.

## Screens and URLs

Initial URLs are documentation targets, not final routing commitments.

| Screen | URL | Purpose |
| --- | --- | --- |
| Platform Dashboard | `/platform` | Overview of tenants and platform health |
| Tenant List | `/platform/tenants` | List and filter tenant businesses |
| Create Tenant | `/platform/tenants/new` | Start tenant creation |
| Tenant Detail | `/platform/tenants/:tenantId` | Inspect tenant profile, status, and setup state |
| Tenant Settings | `/platform/tenants/:tenantId/settings` | Manage platform-owned tenant configuration |
| Tenant Audit | `/platform/tenants/:tenantId/audit` | Review platform-level changes for a tenant |

## Core Workflows

### Create Tenant

1. Platform Owner opens Create Tenant.
2. Platform Owner enters required tenant identity fields.
3. PlatformApp validates uniqueness and required platform constraints.
4. PlatformApp creates the tenant in draft or active state.
5. PlatformApp starts the tenant provisioning flow.

The exact tenant creation requirements are not finalized yet.

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
| Tenant status | Full | Platform lifecycle state |
| Tenant setup state | Full | Tracks readiness/provisioning |
| Tenant owner/admin | Partial | Created or linked during provisioning |
| Tenant limits/features | Full | Future package and entitlement model |
| Tenant audit events | Full | Platform-level audit only |

## Integration Expectations

PlatformApp will eventually interact with domain modules through explicit interfaces.

| Future Module | Expected Use |
| --- | --- |
| Platform / Tenant Registry | Create and manage tenant records |
| Identity and Access | Create or link tenant admin users |
| Entitlements | Manage packages, features, and limits |
| Audit | Record platform-level actions |
| Support Tools | Inspect tenant operational state under controlled permissions |

## Security Rules

- PlatformApp is private and must require platform-owner authentication.
- Tenant users must never access PlatformApp.
- Platform actions must be audited.
- Destructive actions require explicit confirmation.
- Support access to tenant runtime data must be intentional, visible, and permissioned.

## Open Questions

- Which fields are required to create a tenant?
- Is the first tenant admin created during tenant creation or in a separate invitation flow?
- Does a new tenant start as `draft`, `trial`, or `active`?
- Will tenant package/feature limits exist in the first version?
- What support actions can Platform Owner perform inside tenant runtime data?
