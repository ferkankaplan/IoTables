# Module Contracts: Staff Access

Source module: [staff-access.md](staff-access.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `staff_access.upsert_staff_profile` | Provisioning, TenantApp | tenantId, userId, displayName, status | User belongs to tenant; Tenant Admin or Provisioning only | Upsert profile; audit when user-visible | Staff profile |
| `staff_access.disable_staff` | TenantApp | tenantId, userId, reason | Tenant Admin; reason required; cannot disable self; cannot disable the last active tenant admin | Mark user/profile disabled; revoke active roles, station scopes, and hall scopes atomically; audit | Disabled staff profile |
| `staff_access.assign_role` | Provisioning, TenantApp | tenantId, userId, role | Tenant Admin/Provisioning; user belongs to tenant; role supported | Unique active role assignment; duplicate compatible grant returns existing assignment | Active staff role assignment |
| `staff_access.revoke_role` | TenantApp | tenantId, userId, role, reason | Tenant Admin; cannot revoke own last tenant admin role without recovery rule | Mark assignment revoked; audit | Revoked role assignment |
| `staff_access.assign_station` | Provisioning, TenantApp | tenantId, userId, stationId | User has station_staff role or is being provisioned; station belongs to tenant | Unique active station assignment; audit | Active station scope |
| `staff_access.revoke_station` | TenantApp | tenantId, userId, stationId, reason | Tenant Admin; active assignment exists | Mark revoked; audit | Revoked station scope |
| `staff_access.assign_hall` | Provisioning, TenantApp | tenantId, userId, hallId | User has service_staff role or is being provisioned; hall belongs to tenant | Unique active hall assignment; audit | Active hall scope |
| `staff_access.revoke_hall` | TenantApp | tenantId, userId, hallId, reason | Tenant Admin; active assignment exists | Mark revoked; audit | Revoked hall scope |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `staff_access.require_staff_permission` | CashierApp, StationStaffApp, ServiceStaffApp, modules | actor, permission, optional stationId/hallId | Actor session valid; role active; scope assignment active when needed | Success or authorization failure |
| `staff_access.list_staff` | TenantApp | tenantId | Tenant Admin own tenant | Staff profiles, roles, assignments |
| `staff_access.list_authorized_stations` | StationStaffApp, Preparation | actor | station_staff role active | Station IDs actor may operate |
| `staff_access.list_authorized_halls` | ServiceStaffApp, Service Delivery | actor | service_staff role active | Hall IDs actor may operate |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `staff_access.changed` | Role or assignment changes | Staff app guards, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `missing_role` | Actor lacks required staff role. |
| `outside_station_scope` | Station staff attempted to operate unassigned station. |
| `outside_hall_scope` | Service staff attempted to operate unassigned hall. |
| `assignment_target_disabled` | Assignment target is disabled and cannot grant active runtime authority. |
| `self_disable_not_allowed` | Tenant Admin attempted to disable their own staff user from TenantApp. |
| `last_admin_not_allowed` | The operation would remove the last active tenant admin. |
