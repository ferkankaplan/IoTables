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
- Station definitions and lifecycle, owned by Tenant Setup / Station Setup.
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
- A user may hold multiple operational roles in the current release when Tenant Admin explicitly assigns them.
- App actions still require the specific permission for that app and operation.
- A user with both station and service roles must pass station scope checks for StationStaffApp and hall scope checks for ServiceStaffApp independently.
- Cashier permission does not imply tenant admin, station, or service permission.

## Operational Safety

- Permission checks must be server-side.
- Frontend-visible station/hall IDs are not authorization proof.
- Revoked staff permissions must affect active sessions as soon as practical.
- Assignment changes must be audited.
- Staff role, station scope, and hall scope policy is defined in [permission-policy-matrix.md](permission-policy-matrix.md).

## Data Model

| Model / Table | Lifecycle | Key Fields | Invariants / Constraints | History / Deletion |
| --- | --- | --- | --- | --- |
| StaffProfile | active -> disabled | tenant, user, displayName, status | Linked Identity user remains authentication authority; staff profile is tenant-scoped | Disable rather than delete when operational history references the staff user |
| StaffRoleAssignment | active -> revoked | tenant, user, role | Role grants app access only; operation still needs app-specific permission and scope checks | Preserve assignment/revocation history through audit |
| StaffStationAssignment | active -> revoked | tenant, user, station | Station staff can view/update only assigned stations; disabled stations cannot grant active queue authority | Revoke instead of deleting when audit/history matters |
| StaffHallAssignment | active -> revoked | tenant, user, hall | Service staff can view/update only assigned halls; disabled halls cannot grant active delivery authority | Revoke instead of deleting when audit/history matters |

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

None currently.
