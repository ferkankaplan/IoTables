# Module Contracts: Platform / Tenant Registry

Source module: [tenant-registry.md](tenant-registry.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `tenant_registry.register_identity` | Provisioning | name, subdomain, gsmNumber, sector, optional capacity/address | Platform Owner already authorized by Provisioning; name/subdomain/GSM required; subdomain normalized and unique | Insert tenant as `provisioning`; unique lower(subdomain) prevents duplicate tenant | Tenant identity with `tenantId` and `status = provisioning` |
| `tenant_registry.update_profile` | PlatformApp, TenantApp | tenantId, editable profile fields | TenantApp limited to own tenant; name/subdomain/lifecycle/DNS readiness immutable to tenant | Single tenant row update; GSM changes require audit | Updated tenant profile |
| `tenant_registry.change_status` | PlatformApp | tenantId, nextStatus, reason | Platform Owner only; allowed lifecycle transition; reason required for suspend/reactivate/recovery | Lock tenant row; append lifecycle event; audit required | Updated tenant status |
| `tenant_registry.set_dns_ready` | PlatformApp | tenantId, dnsReady | Platform Owner only; manual checklist flag; no DNS automation implied | Lock tenant row; audit required | Updated DNS readiness |
| `tenant_registry.mark_provisioning_failed` | Provisioning | tenantId, safe error summary | Tenant must not be active; error summary must be redacted | Lock tenant row; set `provisioning_failed`; append lifecycle event | Failed provisioning state |
| `tenant_registry.activate_tenant` | Provisioning | tenantId | Required setup records committed; starter application state valid when selected | Lock tenant row; transition `provisioning -> active`; append lifecycle event | Active tenant |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `tenant_registry.resolve_by_subdomain` | TenantApp, CustomerApp, CashierApp, StationStaffApp, ServiceStaffApp | subdomain | Return availability only; runtime modules must block suspended/provisioning tenants | Tenant routing context and lifecycle status |
| `tenant_registry.get_profile` | PlatformApp, TenantApp | tenantId | Platform can read all; TenantApp own tenant only | Tenant identity/profile without runtime data |
| `tenant_registry.get_health` | PlatformApp | tenantId or list filter | Platform Owner only; no tenant runtime detail leakage | Tenant health summary |
| `tenant_registry.get_lifecycle_events` | PlatformApp | tenantId | Platform Owner only | Tenant lifecycle timeline |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `tenant.created` | Tenant identity is registered | Audit, Provisioning |
| `tenant.activated` | Tenant becomes active | Audit, Platform health |
| `tenant.provisioning_failed` | Provisioning failure is recorded | Audit, Platform health |
| `tenant.suspended` | Tenant is suspended | Tenant app guards, Audit |
| `tenant.gsm_changed` | Tenant GSM changes | Audit, future OTP challenges |
| `tenant.profile_updated` | Tenant editable profile fields except GSM-only change | Audit |
| `tenant.dns_ready_changed` | Platform DNS readiness flag changes | PlatformApp, Audit |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `duplicate_subdomain` | Another tenant already owns the normalized subdomain. |
| `immutable_identity` | Caller attempted to change name or subdomain after creation. |
| `invalid_lifecycle_transition` | Requested status change is not allowed from current state. |
| `tenant_runtime_leak` | Query attempted to expose orders/payments/station queues through Platform health. |
