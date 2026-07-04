# PlatformApp UI States
### Primary Workspaces

| Workspace | Required States |
| --- | --- |
| Login | loading, invalid credentials, first password change required |
| Dashboard / Tenant List | loading, empty tenant list, partial health unavailable, tenant row stale, platform auth expired |
| Create Tenant | pristine, validating, submitting, provisioning, provisioning failed, success |
| Tenant Detail | loading, not found, suspended, provisioning, provisioning failed, DNS not ready, health unavailable |
| Tenant Audit | loading, empty audit, filtered empty, access denied |

### Empty States

- Tenant List empty: show that no tenant exists yet and expose Create Tenant.
- Tenant Audit empty: show that no platform-level audit events exist for the selected tenant.
- Tenant health unavailable: show unknown/degraded health without blocking platform metadata access.

### Blocked and Error States

| Case | UI Behavior |
| --- | --- |
| Platform Owner not authenticated | Redirect to login |
| Bootstrap user missing | Show setup unavailable state; do not expose dashboard |
| Tenant create required field missing | Mark field and keep form data |
| Subdomain already exists | Mark subdomain field and block submit |
| Provisioning failed | Show recoverable failure state and audit/retry affordance when available |
| DNS not ready | Show checklist warning, not a runtime mutation |
| Tenant suspended | Show suspended badge and reason where allowed |

### Success and Confirmation States

- Tenant creation success shows tenant identity, subdomain, lifecycle state, starter template state, admin bootstrap state, and DNS checklist.
- Tenant suspension/reactivation requires reason and shows updated lifecycle state after success.
- Tenant GSM update success shows audited sensitive-contact update.

### Stale and Retry States

- If tenant state changes while Tenant Detail is open, refresh visible lifecycle and setup state before allowing another lifecycle command.
- Retrying failed provisioning must use explicit recovery tooling, not normal Create Tenant submit.
- Duplicate Create Tenant submit should stay disabled while pending; backend uniqueness remains authoritative.

### Visual Priority Rules

- Tenant lifecycle state must be visible in tenant lists and details.
- `provisioning_failed`, `suspended`, and DNS-not-ready states need stronger visual priority than normal `active` state.
- Tenant health summary must not visually imply unsupported runtime control.

### Copy Requirements

- Use "tenant unavailable", "setup failed", "DNS not ready", and "provisioning" language.
- Do not claim DNS automation in v1.
- Do not present tenant as a fiscal/POS-complete system.
