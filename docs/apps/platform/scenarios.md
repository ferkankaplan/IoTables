# PlatformApp Scenarios
### P-01: Platform Owner Login

Happy path:

1. Platform Owner opens `https://platform.iotables.net/login`.
2. PlatformApp validates username/password.
3. PlatformApp opens the dashboard.

Branches:

| Branch | Expected Result |
| --- | --- |
| First Platform Owner does not exist | Access is unavailable until explicit bootstrap command creates it |
| Bootstrap password still active | Force password change before dashboard access |
| Invalid credentials | Reject without tenant data exposure |
| Platform user disabled | Reject login |

Result:

- Dashboard is visible only to authenticated Platform Owner.

Ownership:

- PlatformApp + Access.

### P-02: Create Tenant With Cafe Starter

Happy path:

1. Platform Owner enters tenant name, subdomain, GSM number, and optional profile fields.
2. PlatformApp sends tenant-creation OTP to the tenant identity GSM.
3. Platform Owner enters the OTP code.
4. PlatformApp validates required fields, subdomain uniqueness, GSM uniqueness, and OTP proof.
5. PlatformApp submits the create-tenant command to Provisioning.
6. Provisioning registers Tenant in `provisioning`.
7. Provisioning creates tenant admin and starter staff users through Access.
8. Provisioning applies `cafe.v1` through Sector Starter Templates once.
9. Starter data creates halls, tables, stations, products, staff, and default service delivery tracking.
10. Governance records `starter_template.applied`.
11. Provisioning activates tenant after required setup records commit.

Branches:

| Branch | Expected Result |
| --- | --- |
| Required tenant name missing | Reject before provisioning starts |
| Required subdomain missing | Reject before provisioning starts |
| Required GSM missing | Reject before provisioning starts |
| Subdomain already exists | Reject before provisioning starts |
| GSM already belongs to another tenant | Reject before provisioning starts |
| Tenant-creation OTP missing, expired, invalid, or for a different GSM | Reject before provisioning starts |
| Tenant name duplicates an existing tenant | Allowed only if subdomain is unique; name is not trusted identifier |
| Optional sector omitted | Create tenant without starter data unless PlatformApp requires sector selection later |
| Starter application already exists for tenant/template | Do not reapply starter data |
| Starter data transaction fails | Roll back or mark tenant `provisioning_failed`; do not activate |
| Tenant admin creation fails | Roll back or mark tenant `provisioning_failed`; do not activate |
| Audit write fails for critical creation event | Tenant creation must fail or enter recoverable failure according to audit failure policy |

Result:

- Active tenant exists with immutable name/subdomain and editable GSM.
- Starter data is normal tenant-owned data after creation.

Ownership:

- PlatformApp + Platform/Provisioning + Tenant Registry + Access + Sector Starter Templates + Tenant Setup + Governance.

### P-03: Wildcard Tenant Host Availability

Happy path:

1. Deployment config provides the environment wildcard tenant namespace.
2. Platform Owner creates a tenant with a unique subdomain.
3. Provisioning activates the tenant after required setup records commit.
4. The tenant public host is derived from the immutable subdomain and environment root domain.
5. PlatformApp displays the derived tenant host without exposing a tenant-level DNS action.

Branches:

| Branch | Expected Result |
| --- | --- |
| Wildcard DNS missing or misconfigured | Treat as deployment/ops fault; do not create a per-tenant recovery state |
| Tenant subdomain route fails while wildcard environment is healthy | Investigate tenant resolution or runtime routing; Tenant Registry remains the tenant identity source |

Result:

- Tenant host availability is a deployment namespace guarantee, not mutable tenant state.

Ownership:

- PlatformApp + Platform + Ops.

### P-04: Suspend and Reactivate Tenant

Happy path:

1. Platform Owner opens Tenant Detail.
2. Platform Owner suspends tenant with reason.
3. Tenant runtime apps reject normal operation.
4. Platform Owner later reactivates tenant if allowed.

Branches:

| Branch | Expected Result |
| --- | --- |
| Suspend without reason | Reject |
| Tenant already suspended | Return current suspended state idempotently |
| Suspended tenant receives customer order request | Reject and show unavailable state |
| Suspended tenant receives staff/cashier request | Block runtime access |

Result:

- Tenant status controls runtime availability.

Ownership:

- PlatformApp + Platform + Governance.

### P-05: List and Inspect Tenants

Happy path:

1. Platform Owner opens dashboard or Tenant List.
2. PlatformApp lists tenants with identity, subdomain, lifecycle state, setup state, and high-level health.
3. Platform Owner opens Tenant Detail.
4. PlatformApp shows platform-owned tenant metadata, lifecycle, setup state, starter template state, tenant admin bootstrap state, and audit summary.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant provisioning failed | Detail shows failure state and recovery affordance |
| Tenant suspended | Detail shows suspended state and reason/audit |
| Platform Owner attempts runtime mutation from detail | Reject unless explicit support/recovery workflow exists |
| Runtime health signal unavailable | Show unknown/degraded summary without blocking platform metadata view |

Result:

- PlatformApp can inspect platform-owned state without becoming a tenant runtime console.

Ownership:

- PlatformApp + Platform + Governance.

### P-06: Update Tenant GSM

Happy path:

1. Platform Owner or authorized TenantApp path opens editable tenant settings.
2. Actor updates tenant GSM number.
3. Backend validates format and tenant scope.
4. Backend records change and audit.
5. Future tenant admin/cashier OTP challenges use the new GSM.

Branches:

| Branch | Expected Result |
| --- | --- |
| GSM format invalid | Reject |
| Actor not authorized | Reject |
| Same GSM submitted | Return unchanged/idempotent result |
| Active OTP challenge exists for old GSM | Existing challenge should not silently change target; new challenge uses new GSM |

Result:

- Tenant GSM changes are explicit, audited, and affect future sensitive flows.

Ownership:

- PlatformApp or TenantApp + Platform/Tenant Registry + Governance.
