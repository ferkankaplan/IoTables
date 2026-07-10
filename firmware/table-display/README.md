# IoTables Table Display Firmware

This folder contains the generated ESP32 table display firmware template.

`masa000.ino` is the canonical generated output shape for one table. Backend generation must replace every `__IOTABLES_*__` placeholder and then expose the result as a one-time download, for example `masa000.ino`, `masa001.ino`, or the tenant's table naming equivalent.

## Required Generated Values

| Placeholder | Source |
| --- | --- |
| `__IOTABLES_WIFI_SSID__` | TenantApp table creation/provisioning input |
| `__IOTABLES_WIFI_PASSWORD__` | TenantApp table creation/provisioning input |
| `__IOTABLES_TENANT_HOST__` | Tenant subdomain host |
| `__IOTABLES_TABLE_LABEL__` | Table display label |
| `__IOTABLES_DISPLAY_CREDENTIAL__` | Raw display credential returned once by Table Display Provisioning |
| `__IOTABLES_TLS_ROOT_CA_PEM__` | Root CA for the tenant HTTPS endpoint |

## Safety Rules

- Raw WiFi password and raw display credential may appear only in the one-time generated `.ino` response or its short-lived encrypted download artifact.
- Raw display credential must never be stored in database rows, logs, audit events, or customer QR payloads.
- The generated download must expire or be consumed once.
- Re-generating firmware for a table rotates the display credential and revokes the previous active credential.
- TLS verification is mandatory; generated firmware must include the tenant HTTPS root CA.

## Arduino Dependencies

- ESP32 board support package.
- `TFT_eSPI`.
- `QRCode`.

TFT pin mapping belongs to the board profile, not to this IoTables behavior sketch.
