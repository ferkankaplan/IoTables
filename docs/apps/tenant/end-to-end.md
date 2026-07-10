# TenantApp End-to-End Role

This document extracts the parts of the shared current release end-to-end flow where this app participates.

See the full shared flow: [../_shared/canonical-end-to-end.md](../_shared/canonical-end-to-end.md).

### 2. Tenant Admin Configures Operation
1. Tenant Admin opens `https://[tenant].iotables.net/login`.
2. Tenant Admin changes the temporary password and verifies OTP.
3. TenantApp opens the admin workspace.
4. Tenant Admin reviews starter halls, tables, stations, products, staff, and settings.
5. Tenant Admin manages halls and tables from Hall Management.
6. Tenant Admin provisions table displays from table detail panels.
7. Tenant Admin manages stations and menu.
8. Tenant Admin assigns staff roles, station scopes, and service hall scopes.
9. Tenant Admin chooses whether service delivery tracking remains enabled.

Acceptance criteria:

- Tables are managed inside hall context, not as a primary standalone page.
- Each product/service routes to exactly one station in the current release.
- Service delivery tracking is enabled by default for the cafe starter.
- If service delivery tracking is disabled, ServiceStaffApp controls are hidden and `PreparationItem.ready` becomes the final tracked fulfillment state.
- TenantApp cannot edit tenant name or subdomain.

### 3. Table Display Shows Fresh QR
1. Tenant Admin enters WiFi SSID/password while creating or provisioning a table display.
2. Backend rotates the table display credential atomically.
3. Backend renders a one-time table firmware file, for example `masa000.ino`.
4. Tenant Admin downloads and flashes the generated firmware to the ESP32.
5. ESP32 authenticates with the embedded display credential to fetch current QR payloads.
6. Backend resolves tenant/table from the credential.
7. QR token changes at least every 60 seconds and also rotates after redemption.

Acceptance criteria:

- ESP32 is a table display surface, not a separate device inventory aggregate in the current release.
- Only one active display credential exists per tenant/table.
- Re-provisioning revokes the previous active credential.
- Raw display credentials are never embedded in customer QR payloads.
- Raw WiFi password and raw display credential appear only in the one-time generated firmware response.
- Client-sent table IDs are not trusted.
