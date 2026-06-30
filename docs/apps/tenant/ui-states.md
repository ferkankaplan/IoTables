# TenantApp UI States
### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Public Tenant Page | loading, tenant not found, tenant unavailable, public info empty/fallback |
| Tenant Login | loading, invalid credentials, first password change required, OTP required, OTP expired, OTP failed |
| Admin Dashboard | loading, starter data present, setup incomplete, tenant suspended/blocked |
| Hall Management | loading, empty halls, selected hall empty tables, table panel loading, table active-session blocked |
| Station Management | loading, empty stations, station disabled, station has active items blocked |
| Menu Management | loading, empty categories, empty category products, invalid product, unavailable product, disabled product |
| Tenant Settings | loading, immutable field blocked, service tracking changed, GSM changed |
| Staff Management | loading, empty staff, disabled user, missing role/scope, active session permission changed |

### Empty States

- Empty halls: expose Create Hall.
- Hall without tables: expose Create Table inside hall context.
- Empty stations: expose Create Station before menu products can become orderable.
- Empty menu category: expose Create Product/Service.
- Empty staff list: expose Create Staff User, while preserving starter staff if present.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| Tenant not active | Block admin/runtime surfaces according to tenant state |
| Tenant admin first login incomplete | Force password change and OTP flow |
| OTP expired | Allow new OTP challenge |
| Tenant name/subdomain edit attempted | Show immutable field state and prevent edit |
| Table has active TableSession | Block normal disable/delete; require explicit recovery workflow if later added |
| Product has no station | Product cannot be orderable |
| Product assigned to disabled station | Product cannot remain orderable |
| Product has more than one station | Reject in v1 |
| Service tracking disabled | Hide ServiceStaffApp controls and explain ready-as-final operational mode |
| Staff user lacks scope | Show no operational scope warning for affected app role |

### Success and Confirmation States

- Halls/tables save in context without leaving Hall Management.
- Table display provisioning shows claim created, waiting for device, provisioned, revoked/re-provisioned states.
- Menu save shows product availability/orderability state.
- Service delivery tracking change shows immediate impact on ServiceStaffApp and customer-visible status semantics.
- Staff scope changes show which apps the user can access.

### Stale and Retry States

- If a table/session state changes while table panel is open, disable stale destructive actions and refresh.
- If station/product availability changes during edit, save must revalidate server-side and show field-level conflicts.
- If staff permission changes while user is active, next action must enforce updated scope; UI should refresh scope state when detected.

### Visual Priority Rules

- Hall/table management should keep selected hall and table context visible while panels are open.
- Disabled records must be visually distinct from orderable/active records.
- Service delivery tracking disabled mode must be visible in settings and not hidden as a minor toggle.
- Product orderability state must be clear when station, availability, or required modifier setup blocks ordering.

### Copy Requirements

- Use "disabled" for historical records that remain for integrity.
- Use "unavailable" for temporarily not orderable products/stations.
- Do not imply starter data is protected system data after creation.
- Do not expose platform setup internals on the public tenant page.
