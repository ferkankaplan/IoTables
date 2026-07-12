# API Contracts: Staff Access

Source contracts: [staff-access-contracts.md](staff-access-contracts.md)
Shared rules: [../_shared/api-contract-format.md](../_shared/api-contract-format.md)

Staff Access owns staff profiles, role assignments, station scope, and hall scope.

## Endpoints

| Method | Path | App / Caller | Module Contract | Auth | Request | Success | Failure Codes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GET` | `/api/tenant-setup/staff` | TenantApp | `staff_access.list_staff` | Tenant Admin session | none | `StaffList` | `not_authorized` |
| `POST` | `/api/tenant-setup/staff` | TenantApp | `identity_access.create_bootstrap_user` + `staff_access.upsert_staff_profile` + `staff_access.assign_role` + conditional station/hall assignments | Tenant Admin session + CSRF | Body: `CreateStaffRequest` | `StaffProfile` | `duplicate_username`, `validation_failed`, `assignment_target_disabled` |
| `POST` | `/api/tenant-setup/staff/{userId}/disable` | TenantApp | `staff_access.disable_staff` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `not_found_or_hidden`, `self_disable_not_allowed`, `last_admin_not_allowed` |
| `PATCH` | `/api/tenant-setup/staff/{userId}/profile` | TenantApp | `staff_access.upsert_staff_profile` | Tenant Admin session + CSRF | Body: `displayName`, `status` | `StaffProfile` | `not_authorized`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/staff/{userId}/roles` | TenantApp | `staff_access.assign_role` | Tenant Admin session + CSRF | Body: `role` | `StaffProfile` | `assignment_target_disabled`, `validation_failed` |
| `POST` | `/api/tenant-setup/staff/{userId}/roles/{role}/revoke` | TenantApp | `staff_access.revoke_role` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `last_admin_not_allowed` |
| `POST` | `/api/tenant-setup/staff/{userId}/stations` | TenantApp | `staff_access.assign_station` | Tenant Admin session + CSRF | Body: `stationId` | `StaffProfile` | `outside_station_scope`, `validation_failed` |
| `POST` | `/api/tenant-setup/staff/{userId}/stations/{stationId}/revoke` | TenantApp | `staff_access.revoke_station` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `not_found_or_hidden` |
| `POST` | `/api/tenant-setup/staff/{userId}/halls` | TenantApp | `staff_access.assign_hall` | Tenant Admin session + CSRF | Body: `hallId` | `StaffProfile` | `outside_hall_scope`, `validation_failed` |
| `POST` | `/api/tenant-setup/staff/{userId}/halls/{hallId}/revoke` | TenantApp | `staff_access.revoke_hall` | Tenant Admin session + CSRF | Body: `reason` | `StaffProfile` | `reason_required`, `not_found_or_hidden` |
| `GET` | `/api/station-staff/authorized-stations` | StationStaffApp | `staff_access.list_authorized_stations` | StationStaff session | none | `AuthorizedStationList` | `missing_role` |
| `GET` | `/api/service-staff/authorized-halls` | ServiceStaffApp | `staff_access.list_authorized_halls` | ServiceStaff session | none | `AuthorizedHallList` | `missing_role` |

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
| `roles` | string enum array | yes | One or more of `tenant_admin`, `cashier`, `station_staff`, `service_staff`. |
| `stationIds` | string array | conditional | Allowed only with `station_staff`; grants active station scope. |
| `hallIds` | string array | conditional | Allowed only with `service_staff`; grants active hall scope. |

Staff first-password setup requires OTP sent to the platform-owned tenant identity GSM. Password reset OTP uses the platform-owned tenant identity GSM, so `CreateStaffRequest` does not collect a personal staff GSM number.

TenantApp-created staff use the default bootstrap password `12345678`. That password is never returned by API responses and is stored only as a password hash. The first successful login with the default password must return `first_password_required`; setup completion requires the OTP challenge issued to the platform-owned tenant identity GSM.

Creating staff with initial role/scope assignments is one atomic API command from TenantApp's point of view. If any requested role, station assignment, or hall assignment is invalid, the user/profile creation must roll back or return a failed result without leaving a half-created operational staff user.

## Response Schemas

`StaffProfile` includes `userId`, `username`, `displayName`, `status`, `roles`, `stationIds`, `hallIds`, `firstPasswordRequired`, `createdAt`, and `updatedAt`.

`StaffList` uses list envelope with `StaffProfile` items.

## Idempotency

Role and scope assignment commands are naturally idempotent for compatible duplicate grants through unique active assignment constraints. Revokes do not require `Idempotency-Key`; they are state-guarded and audited.
