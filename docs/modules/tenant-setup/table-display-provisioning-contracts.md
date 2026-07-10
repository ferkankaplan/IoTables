# Module Contracts: Table Display Provisioning

Source module: [table-display-provisioning.md](table-display-provisioning.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `table_display.generate_firmware` | TenantApp | tenantId, tableId, wifiSsid, wifiPassword | Tenant Admin; table belongs to tenant and is enabled; WiFi fields are present for generation | Lock table credentials; revoke previous active credential; create new credential hash; render one-time `.ino`; store safe metadata only | One-time `.ino` firmware content returned once |
| `table_display.revoke_credential` | TenantApp | tableId or credentialId, reason | Tenant Admin; credential belongs to tenant/table | Mark credential revoked; audit | Revoked credential state |
| `table_display.rotate_credential` | TenantApp firmware generation flow | tableId | Tenant Admin | Lock table credentials; revoke old active before new active | New active credential |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `table_display.authenticate_credential` | ESP32 QR fetch flow, Table Presence | raw credential secret | Hash match; active; table and tenant enabled | Trusted tenant/table display context |
| `table_display.get_display_state` | TenantApp | tableId | Tenant Admin own tenant | Credential and firmware package status without raw secrets |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `table_display.provisioned` | Firmware package is generated and credential is issued/rotated | Audit, support state |
| `table_display.revoked` | Credential is revoked | Audit, QR fetch guards |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `firmware_download_expired` | One-time firmware download is no longer usable. |
| `firmware_download_consumed` | One-time firmware download was already retrieved. |
| `firmware_download_invalid` | Download token does not match the firmware artifact. |
| `credential_revoked` | Display credential cannot fetch QR. |
| `wrong_table_or_tenant` | Credential-derived table context does not match allowed state. |
