# TenantApp Scenarios
### T-01: Public Tenant Page

Happy path:

1. Visitor opens `https://[tenant].iotables.net/`.
2. TenantApp resolves tenant by subdomain.
3. TenantApp shows safe public tenant fields.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant does not exist | Show not-found/unavailable page |
| Tenant is suspended | Show tenant unavailable |
| Tenant is provisioning/provisioning_failed | Do not expose admin/runtime details |
| Visitor attempts admin action from public page | Require login route |

Result:

- Public page never exposes staff, session, order, payment, setup checklist, or operational internals.

Ownership:

- TenantApp + Platform read.

### T-02: Tenant Admin First Login

Happy path:

1. Tenant Admin opens `/login`.
2. Tenant Admin enters username and temporary password.
3. TenantApp forces password change.
4. TenantApp opens admin dashboard.

Branches:

| Branch | Expected Result |
| --- | --- |
| Invalid temporary password | Reject |
| Password change uses rejected password | Reject |
| User already completed first login | Normal login path, no bootstrap password access |

Result:

- Tenant admin has a non-bootstrap credential.

Ownership:

- TenantApp + Access.

### T-03: Configure Halls and Tables

Happy path:

1. Tenant Admin opens Hall Management.
2. Tenant Admin creates/edits halls.
3. Tenant Admin selects a hall.
4. Tenant Admin creates/edits/reorders/disables tables in the same workspace.
5. Selecting a table opens a contextual panel.

Branches:

| Branch | Expected Result |
| --- | --- |
| Hall name missing | Reject before save |
| Table name missing | Reject before save |
| Reorder request has duplicate order positions | Server normalizes or rejects according to implementation contract |
| Table has historical sessions/orders | Hard delete is unavailable; disable instead |
| Table has active TableSession | Disable must be blocked or require explicit recovery workflow; normal disable cannot strand an active session |
| Tenant Admin tries standalone table management page | Not a primary current release page; use hall workspace/panel |

Result:

- Venue structure remains coherent and table history remains intact.

Ownership:

- TenantApp + Venue Layout + Governance.

### T-04: Provision Table Display

Happy path:

1. Tenant Admin opens a table detail panel.
2. TenantApp creates a short-lived one-time display claim.
3. ESP32 setup consumes the claim.
4. Backend returns display credential once.
5. Table panel shows provisioned display state.

Branches:

| Branch | Expected Result |
| --- | --- |
| Claim expires before use | Claim is rejected; Tenant Admin can create a new claim |
| Claim is reused | Reject |
| Claim belongs to another table | Reject |
| Table is disabled | Reject provisioning unless explicit recovery allows it |
| Table already has active credential | Re-provisioning revokes previous credential and creates a new active one |
| ESP32 loses credential | Tenant Admin re-provisions table display |

Result:

- One active display credential exists per tenant/table.

Ownership:

- TenantApp + Table Display Provisioning.

### T-05: Configure Service Delivery Tracking

Happy path:

1. Tenant Admin opens Tenant Settings.
2. Tenant Admin enables or disables service delivery tracking.
3. TenantApp records setting change and audit.
4. Staff apps adapt to the setting.

Branches:

| Branch | Expected Result |
| --- | --- |
| Enabled | ServiceStaffApp queue is available to authorized service staff |
| Disabled | ServiceStaffApp queue and mutation controls are hidden/blocked |
| Disabled while ready items exist | DeliveryState stops being required; `ready` is final tracked fulfillment from that point |
| Re-enabled later | New ready items can flow through ServiceStaffApp; historical disabled-mode items are not retroactively delivered |

Result:

- Customer-visible status semantics follow current service delivery tracking mode.

Ownership:

- TenantApp + Tenant Setup + Fulfillment read.

### T-06: Configure Menu and Station Routing

Happy path:

1. Tenant Admin creates categories.
2. Tenant Admin creates product/services.
3. Tenant Admin sets descriptions, variants/portions, prices, modifiers, availability overrides, and one station assignment.
4. CustomerApp reads available menu.
5. Ordering validates cart against current menu at submit time.

Branches:

| Branch | Expected Result |
| --- | --- |
| Product has no station | Product cannot be orderable |
| Product has more than one station | Reject in the current release |
| Product disabled | Historical orders remain; product cannot be ordered |
| Product unavailable | Product may be visible but not orderable |
| Price changes | Existing OrderItem snapshots do not change |
| Required modifier missing | Cart item invalid |
| Modifier becomes unavailable before submit | Submit rejects affected item and preserves cart |

Result:

- Menu is the source for current orderability and pricing; order snapshots preserve history.

Ownership:

- TenantApp + Menu Catalog + Governance.

### T-07: Configure Stations

Happy path:

1. Tenant Admin opens Station Management.
2. Tenant Admin reviews starter stations.
3. Tenant Admin creates or edits station name and availability.
4. Tenant Admin disables stations no longer used.
5. Menu Catalog uses enabled stations for product/service assignment.

Branches:

| Branch | Expected Result |
| --- | --- |
| Station name missing | Reject |
| Station has active preparation items | Disable must be blocked or require explicit recovery/workflow |
| Product/service still routes to disabled station | Product/service cannot remain orderable until rerouted or disabled |
| Station staff assigned to disabled station | Assignment remains historical/configured but cannot grant active queue operations |

Result:

- Station setup remains compatible with menu routing and preparation queues.

Ownership:

- TenantApp + Tenant Setup + Menu Catalog/Fulfillment read + Governance.

### T-08: Configure Tenant Settings

Happy path:

1. Tenant Admin opens Tenant Settings.
2. Tenant Admin edits allowed mutable fields:
   - public display name,
   - GSM number,
   - address,
   - capacity,
   - sector classification,
   - service delivery tracking.
3. Backend validates tenant scope and immutable fields.
4. Backend records audit for sensitive/customer-visible changes.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant Admin edits tenant name | Reject |
| Tenant Admin edits subdomain | Reject |
| Sector changes after creation | Update classification only; do not rerun starter data |
| Capacity changes | Update informational field; no entitlement enforcement in the current release |
| Public display name omitted | Public page falls back to immutable tenant name |
| GSM changes | Audit and use new GSM for future OTP challenges |

Result:

- Tenant settings remain mutable only where current release allows.

Ownership:

- TenantApp + Tenant Registry + Tenant Setup + Governance.

### T-09: Review Starter Data

Happy path:

1. Tenant Admin logs in after tenant creation.
2. TenantApp shows starter halls, tables, stations, menu items, staff, and service tracking setting as normal tenant data.
3. Tenant Admin edits, disables, deletes where allowed, or extends starter data.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant Admin deletes starter product before orders exist | Allowed if normal menu rules allow deletion/disable |
| Starter product has historical orders | Hard delete unavailable; disable/preserve history |
| Tenant Admin removes starter hall with active tables/sessions | Reject or require explicit recovery workflow |
| App restart/deploy occurs after edits | Starter data must not be recreated |
| New starter template version exists | Existing tenant does not receive it automatically |

Result:

- Starter data is not special after creation, and provisioning remains one-time.

Ownership:

- TenantApp + Sector Starter Templates read + Tenant Setup + Governance.

### T-10: Configure Staff Access

Happy path:

1. Tenant Admin creates or reviews staff users.
2. Tenant Admin assigns app roles.
3. Tenant Admin assigns station scopes for station staff.
4. Tenant Admin assigns hall scopes for service staff.
5. Staff apps enforce scopes server-side.

Branches:

| Branch | Expected Result |
| --- | --- |
| User has cashier role only | Can enter CashierApp only |
| User has station role without station scope | StationStaffApp shows no operational station access |
| User has service role without hall scope | ServiceStaffApp shows no operational hall access |
| User has multiple roles | Each app checks its own role and scope independently |
| User disabled | Existing sessions stop working as soon as practical |
| Tenant Admin changes scope while staff is active | Next action must enforce updated scope server-side |

Result:

- Staff access is tenant-scoped, app-scoped, and server-authorized.

Ownership:

- TenantApp + Staff Access + Access + Governance.
