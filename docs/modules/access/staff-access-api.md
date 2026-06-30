# API Contracts: Staff Access

Source contracts: [staff-access-contracts.md](staff-access-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Staff Access owns staff profiles, role assignments, station scope, and hall scope.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/v1/tenant/staff` | TenantApp | `staff_access.list_staff` | Tenant Admin session | Query: `status?`, `role?`, `cursor`, `limit` | `StaffList` | `not_authorized` |
| `POST` | `/api/v1/tenant/staff` | TenantApp | `identity_access.create_bootstrap_user` + `staff_access.upsert_staff_profile` + `staff_access.assign_role` + conditional station/hall assignments | Tenant Admin session + CSRF | Body: `CreateStaffRequest` | `StaffProfile` | `duplicate_username`, `validation_failed`, `assignment_target_disabled` |
| `PATCH` | `/api/v1/tenant/staff/{userId}/profile` | TenantApp | `staff_access.upsert_staff_profile` | Tenant Admin session + CSRF | Body: `displayName`, `status` | `StaffProfile` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/v1/tenant/staff/{userId}/roles` | TenantApp | `staff_access.assign_role` | Tenant Admin session + CSRF | Body: `role` | `StaffProfile` | `assignment_target_disabled`, `validation_failed` |
| `POST` | `/api/v1/tenant/staff/{userId}/roles/{role}/revoke` | TenantApp | `staff_access.revoke_role` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `last_admin_not_allowed` |
| `POST` | `/api/v1/tenant/staff/{userId}/stations` | TenantApp | `staff_access.assign_station` | Tenant Admin session + CSRF | Body: `stationId` | `StaffProfile` | `outside_station_scope`, `validation_failed` |
| `POST` | `/api/v1/tenant/staff/{userId}/stations/{stationId}/revoke` | TenantApp | `staff_access.revoke_station` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `not_found_or_hidden` |
| `POST` | `/api/v1/tenant/staff/{userId}/halls` | TenantApp | `staff_access.assign_hall` | Tenant Admin session + CSRF | Body: `hallId` | `StaffProfile` | `outside_hall_scope`, `validation_failed` |
| `POST` | `/api/v1/tenant/staff/{userId}/halls/{hallId}/revoke` | TenantApp | `staff_access.revoke_hall` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `not_found_or_hidden` |
| `GET` | `/api/v1/station-staff/authorized-stations` | StationStaffApp | `staff_access.list_authorized_stations` | StationStaff session | none | `AuthorizedStationList` | `missing_role` |
| `GET` | `/api/v1/service-staff/authorized-halls` | ServiceStaffApp | `staff_access.list_authorized_halls` | ServiceStaff session | none | `AuthorizedHallList` | `missing_role` |

## Internal-Only Contracts

| Module Contract | HTTP Exposure |
| --- | --- |
| `staff_access.require_staff_permission` | Gateway/module guard only. Every business endpoint must call it server-side when staff role/scope matters. |

## Request Schemas

`CreateStaffRequest`:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `username` | string | yes | Unique inside tenant. |
| `displayName` | string | yes | Operational display name. |
| `role` | string enum | yes | `tenant_admin`, `cashier`, `station_staff`, `service_staff`, or other supported v1 staff role. |
| `stationIds` | string array | conditional | Required when role needs station scope. |
| `hallIds` | string array | conditional | Required when role needs hall scope. |

Cashier first-password OTP uses the tenant GSM in v1. `CreateStaffRequest` does not collect a personal staff GSM number.

Creating staff with initial role/scope assignments is one atomic API command from TenantApp's point of view. If any requested role, station assignment, or hall assignment is invalid, the user/profile creation must roll back or return a failed result without leaving a half-created operational staff user.

## Response Schemas

`StaffProfile` includes `userId`, `username`, `displayName`, `status`, `roles`, `stationIds`, `hallIds`, `firstPasswordRequired`, and `disabledAt`.

`StaffList` uses list envelope with `StaffProfile` items.

## Idempotency

Role and scope assignment commands are naturally idempotent for compatible duplicate grants through unique active assignment constraints. Revokes do not require `Idempotency-Key`; they are state-guarded and audited.
