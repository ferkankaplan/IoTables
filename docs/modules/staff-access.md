# Module: Staff Access

## Purpose

Staff Access owns tenant staff roles, app access mapping, station assignment, and service hall assignment.

Identity and Access authenticates users; Staff Access decides what tenant operational scope those staff users may operate.

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Staff role | Authorization concept | assign and revoke |
| Station assignment | Permission | assign station staff to stations |
| Service hall assignment | Permission | assign service staff to halls |
| App access mapping | Policy | cashier/station/service/admin access |

## Not Owned

- Passwords and login sessions.
- Tenant identity.
- Halls/tables themselves.
- Stations themselves.
- Payments, orders, or delivery state.

## Users and App Access

| App / Actor | Access | Limits |
| --- | --- | --- |
| TenantApp / Tenant Admin | manage staff roles and assignments | Own tenant |
| CashierApp / Cashier | use cashier permission | Own tenant |
| StationStaffApp / Station Staff | use assigned station permissions | Authorized stations only |
| ServiceStaffApp / Service Staff | use assigned hall permissions | Authorized halls only |

## Public Interface

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Assign role | Grant app-level access | TenantApp |
| Assign station | Grant station queue scope | TenantApp, StationStaffApp |
| Assign service hall | Grant delivery hall scope | TenantApp, ServiceStaffApp |
| Require staff permission | Guard staff actions | Staff apps |

## Internal Rules

- Cashier role is required for CashierApp actions.
- Station staff can only view/update assigned stations.
- Service staff can only view/update assigned halls.
- Tenant admin manages staff access from TenantApp.
- Starter staff are normal tenant staff after provisioning.

## Operational Safety

- Permission checks must be server-side.
- Frontend-visible station/hall IDs are not authorization proof.
- Revoked staff permissions must affect active sessions as soon as practical.
- Assignment changes must be audited.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| StaffProfile | Tenant staff metadata | linked to Identity user |
| StaffRoleAssignment | App role access | cashier, station, service, admin |
| StaffStationAssignment | Station permission | station-scoped |
| StaffHallAssignment | Service permission | hall-scoped |

## App Surfaces

| App | Usage |
| --- | --- |
| TenantApp | Manage roles and assignments |
| CashierApp | Enforce cashier permission |
| StationStaffApp | Enforce station assignment |
| ServiceStaffApp | Enforce hall assignment |

## Future Service Boundary

- Own data: staff profiles, roles, station/hall assignments.
- Own APIs: assign/revoke role, check permission, list authorized scopes.
- Published events: staff_access.changed.
- Consumed events: user.disabled, hall.disabled, station.disabled.
- Must not leak: operational permissions to client-side checks only.

## Open Questions

- Whether a user can hold multiple operational roles simultaneously in v1.
