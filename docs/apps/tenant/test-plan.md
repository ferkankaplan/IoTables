# TenantApp Test Plan

This document defines TenantApp-visible test coverage for the current release. It does not replace module, database, API, security, or implementation tests. Executable tests must reference the owning semantic source when implementation begins.

Source context:

- [definition.md](definition.md)
- [end-to-end.md](end-to-end.md)
- [scenarios.md](scenarios.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [ui-states.md](ui-states.md)
- [visibility.md](visibility.md)
- [api-usage.md](api-usage.md)
- [wireframes.md](wireframes.md)
- [copy.md](copy.md)
- [components.md](components.md)
- [../_shared/accessibility-responsive.md](../_shared/accessibility-responsive.md)
- [../_shared/copy-style.md](../_shared/copy-style.md)
- [../../testing/strategy.md](../../testing/strategy.md)

## Test Scope

TenantApp tests prove that a Tenant Admin can complete first login, configure tenant setup, manage halls/tables, provision table displays, configure stations/menu/staff/settings, and review setup audit without gaining platform, cashier, station, service, or customer-ordering authority.

Out of scope for this test plan:

- platform tenant creation/suspension;
- customer order creation;
- cashier payment/correction/session-close mutation;
- station preparation mutation;
- service delivery mutation;
- fiscal/e-Adisyon/ÖKC;
- hardware printer/cash drawer/payment terminal setup;
- floor-plan coordinate editor;
- package/courier/pickup/phone/marketplace/counter-sale/stock/multi-location setup.

## Happy Path Coverage

| Scenario | Coverage |
| --- | --- |
| T-01 Public Tenant Page | Public page shows safe tenant fields only. |
| T-02 Tenant Admin First Login | Tenant Admin changes bootstrap password with tenant-GSM OTP. |
| T-03 Configure Halls and Tables | Tenant Admin manages halls/tables in one workspace with contextual table panel. |
| T-04 Provision Table Display | Tenant Admin enters WiFi data, generates one-time firmware, downloads it, and panel shows provisioned state. |
| T-05 Configure Service Delivery Tracking | Tenant Admin enables/disables tracking and UI explains staff/customer impact. |
| T-06 Configure Menu and Station Routing | Tenant Admin configures categories/products/variants/modifiers/prices/availability/one station assignment. |
| T-07 Configure Stations | Tenant Admin creates/updates/disables stations safely. |
| T-08 Configure Tenant Settings | Tenant Admin edits allowed mutable profile and operational settings only. |
| T-09 Review Starter Data | Starter records are editable normal tenant data and do not regenerate after edits. |
| T-10 Configure Staff Access | Tenant Admin manages staff roles, station scopes, and hall scopes. |

## Branch Coverage

### Public Page and Login

| Branch | Expected Test Result |
| --- | --- |
| Tenant missing | Safe unavailable/not-found public page. |
| Tenant suspended/provisioning/provisioning_failed | No admin/runtime details exposed. |
| Visitor attempts admin action | Login required. |
| Invalid temporary password | Reject safely. |
| Rejected new password | Password policy error. |
| Password reset OTP expired | New OTP challenge allowed. |
| Password reset OTP locked/too many attempts | Locked/slow state shown. |
| Tenant GSM changed before password reset verification | New challenge uses current platform-owned tenant identity GSM. |
| First login already completed | Bootstrap password cannot continue; normal login path. |

### Halls, Tables, and Display

| Branch | Expected Test Result |
| --- | --- |
| Hall name missing | Reject before save. |
| Table name missing | Reject before save. |
| Duplicate/reordered positions conflict | Server normalization/rejection visible. |
| Table has historical sessions/orders | Hard delete absent; disable/preserve history. |
| Table has active TableSession | Normal disable blocked. |
| Standalone table management attempted | Not a primary current release page; hall workspace used. |
| Display firmware download expires | Download rejected; new firmware can be generated. |
| Display firmware download reused | Rejected safely. |
| Display firmware wrong table context | Rejected safely. |
| Disabled table provisioning | Rejected unless explicit recovery later exists. |
| Re-provision active display | Previous credential revoked; new active credential created. |

### Stations, Menu, and Service Tracking

| Branch | Expected Test Result |
| --- | --- |
| Station name missing | Reject before save. |
| Station has active preparation items | Disable blocked. |
| Product still routes to disabled station | Product cannot remain orderable. |
| Product has no station | Product cannot be orderable. |
| Product has more than one station | Rejected in the current release. |
| Product disabled | Historical orders preserved; product not orderable. |
| Product unavailable | Product may be visible but not orderable. |
| Price changes | Existing OrderItem snapshots unchanged. |
| Required modifier missing/invalid | Product/cart validation catches invalid setup. |
| Service tracking disabled while ready items exist | Ready becomes final tracked fulfillment from that point; no retroactive delivery mutation. |
| Service tracking re-enabled | New ready items can flow through ServiceStaffApp; old disabled-mode items are not retroactively delivered. |

### Settings, Staff, and Starter Data

| Branch | Expected Test Result |
| --- | --- |
| Tenant name edit attempted | Rejected/blocked as immutable. |
| Subdomain edit attempted | Rejected/blocked as immutable. |
| Sector changed after creation | Classification updates; starter data does not rerun. |
| Capacity changed | Informational update only; no entitlement enforcement. |
| Public display name omitted | Public page falls back to tenant name. |
| GSM edit attempted in TenantApp | Blocked; only PlatformApp can change platform-owned tenant identity GSM. |
| Starter record deleted/disabled | Does not regenerate after restart/deploy. |
| New starter template version exists | Existing tenant does not receive it automatically. |
| Staff role without required scope | Affected app shows no operational access. |
| Multiple roles | Each runtime app checks its own role/scope. |
| User disabled | Existing sessions stop working as soon as practical. |
| Scope changed while active | Next action enforces updated scope server-side. |

## Acceptance Criteria Coverage

| Acceptance Criterion | Test Evidence |
| --- | --- |
| Public page exposes only safe fields | Browser/API visibility tests. |
| Tenant admin first login requires password change with tenant-GSM OTP | Browser login and first-password API tests. |
| Tenant name/subdomain not editable | UI blocked state and API rejection. |
| Halls/tables one workspace with contextual table panels | Browser E2E and forbidden route/control checks. |
| Current release table layout ordered grid, not floor-plan coordinates | UI absence and copy checks. |
| Table display provisioning from table detail | Browser/API tests for firmware generation and one-time download lifecycle. |
| Stations can be created/disabled | UI/API tests with disable blockers. |
| Menu setup supports variants/modifiers/prices/availability/one station | Component/API tests. |
| Each product/service has exactly one station | Validation tests. |
| Service delivery tracking can be enabled/disabled | Settings/API/visibility tests. |
| Staff roles/scopes can be managed | Staff API/browser tests. |
| Critical configuration changes are audited | Audit API and event tests. |

## UI State Coverage

Every state in [ui-states.md](ui-states.md) requires a UI test or documented non-UI API test.

| Surface | Required UI States |
| --- | --- |
| Public Tenant Page | loading, tenant not found, tenant unavailable, public info empty/fallback |
| Tenant Login | loading, invalid credentials, first password change required |
| Admin Dashboard | loading, starter data present, setup incomplete, tenant suspended/blocked |
| Hall Management | loading, empty halls, selected hall empty tables, table panel loading, table active-session blocked |
| Station Management | loading, empty stations, station disabled, station has active items blocked |
| Menu Management | loading, empty categories, empty category products, invalid product, unavailable product, disabled product |
| Tenant Settings | loading, immutable field blocked, service tracking changed, GSM read-only |
| Staff Management | loading, empty staff, disabled user, missing role/scope, active session permission changed |

## API Usage Coverage

TenantApp executable tests must cover the app-visible behavior of these endpoints:

| Endpoint | Required Coverage |
| --- | --- |
| `GET /api/tenant/context` | Public-safe context only; tenant unavailable states. |
| `GET /api/auth/login-requirements` | First-login/setup requirement discovery. |
| `POST /api/auth/login` | Tenant admin login, wrong app scope, first-password required. |
| `GET /api/auth/session` | Protected admin route access. |
| `POST /api/auth/logout` | Session revocation. |
| `POST /api/auth/first-password/begin` | Setup-token and OTP-required password-change state. |
| `POST /api/auth/first-password/complete` | Password policy and setup-token validation. |
| `GET/POST /api/auth/otp-challenges/{challengeId}...` | Password reset OTP state, send, verify, expired, locked. |
| `GET /api/tenant/profile` | Read-only tenant profile; identity GSM not mutable from TenantApp. |
| `GET/PATCH /api/tenant-setup/operational-settings` | Public display and service tracking mode. |
| `GET /api/tenant/starter-template-application` | Read-only starter proof. |
| `GET/POST /api/tenant-setup/staff...` | Staff list/create with role/scope assignment and rollback. |
| `GET /api/tenant-setup/venue/board` | Hall/table board and empty states. |
| `/api/tenant-setup/halls...` | Hall create/update/disable blockers. |
| `/api/tenant-setup/tables...` | Table create/update/disable/context blockers. |
| `/api/tenant-setup/stations...` | Station create/update/disable blockers. |
| `/api/tenant-setup/menu...` | Menu/category/product/variant/modifier/availability/routing validation. |
| `/api/tenant-setup/tables/{tableId}/display...` | Firmware generation/download, display state, revoke, rotate. |
| `GET /api/tenant/audit-events` | Tenant setup/security audit only. |

## Security and Abuse Coverage

Required tests:

- tenant context is resolved from host/session, not body/query tenant IDs;
- tenant admin cannot cross tenants;
- tenant users cannot access PlatformApp or other tenant hosts;
- unsafe TenantApp requests require CSRF;
- raw OTP codes, WiFi passwords, generated firmware content, and display credentials are never logged or returned after one-time reveal;
- table display firmware generation and download are atomic and one-time;
- credential rotation revokes the previous active credential;
- staff role/scope changes are enforced server-side on next action;
- disabled users cannot keep using existing sessions beyond allowed enforcement window;
- TenantApp cannot call runtime mutation APIs for orders, payments, sessions, preparation, delivery, or customer carts.

## Accessibility and Responsive Coverage

Required checks:

- public page, login, OTP, hall/table, display provisioning, station, menu, staff, settings, and audit flows work by keyboard;
- drawers/dialogs trap and restore focus;
- ordered table grid has readable table labels and selected state;
- disable/revoke dialogs identify object and reason requirement;
- status badges and blockers have text alternatives;
- mobile fallback keeps workspaces usable as stacked layouts;
- tablet/desktop panels do not overlap table names, product names, station labels, staff roles, or warnings.

## Copy Coverage

Tests must assert that:

- public page copy reveals no admin/runtime internals;
- login/OTP copy uses [copy.md](copy.md);
- hall/table copy does not imply standalone table management;
- menu copy distinguishes disabled and unavailable;
- service tracking copy states ServiceStaffApp/customer/cashier impact;
- display provisioning copy explains one-time secret behavior;
- forbidden runtime and unsupported current release claims from [copy.md](copy.md) are absent.

## Forbidden Control Coverage

TenantApp tests must prove these controls are absent:

- standalone primary table management page;
- floor-plan coordinate editor;
- customer order creation;
- payment receive/void/provider checkout;
- close table session;
- station preparation actions;
- service delivery actions;
- tenant creation/suspension;
- fiscal/e-Adisyon/ÖKC setup;
- printer, terminal, cash drawer, stock/recipe, package/courier/pickup/phone/marketplace/counter-sale/multi-location setup.

## Traceability

When implementation begins:

- browser E2E tests should reference TenantApp scenarios T-01 through T-10;
- API tests should reference [api-usage.md](api-usage.md) and module API contracts;
- table display race tests should reference table-display provisioning and QR flow sources;
- UI component tests should reference [wireframes.md](wireframes.md), [components.md](components.md), and [ui-states.md](ui-states.md);
- copy tests should reference [copy.md](copy.md).

If a test exposes a product ambiguity, update the owning app or module documentation before changing the test expectation.

## Acceptance Gate

TenantApp is ready for implementation only when:

- all happy paths and branches above have an owner test layer;
- hall/table, display provisioning, menu routing, staff scope, and service tracking safety coverage are defined;
- first-login OTP-required coverage is defined;
- UI state and copy coverage are defined;
- forbidden TenantApp runtime controls are explicitly tested absent;
- semantic index is regenerated after this document changes.
