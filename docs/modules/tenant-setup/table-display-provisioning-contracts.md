# Module Contracts: Table Display Provisioning

Source module: [table-display-provisioning.md](table-display-provisioning.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `table_display.create_claim` | TenantApp | tenantId, tableId | Tenant Admin; table belongs to tenant and is enabled | Insert short-lived claim hash; audit | One-time display claim secret returned once |
| `table_display.consume_claim` | ESP32 setup flow | raw claim secret | Claim hash exists, unexpired, unconsumed | Atomic consume; revoke previous active credential; insert new credential hash | Display credential secret returned once |
| `table_display.revoke_credential` | TenantApp | tableId or credentialId, reason | Tenant Admin; credential belongs to tenant/table | Mark credential revoked; audit | Revoked credential state |
| `table_display.rotate_credential` | TenantApp, consume claim flow | tableId | Tenant Admin or claim consumption | Lock table credentials; revoke old active before new active | New active credential |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `table_display.authenticate_credential` | ESP32 QR fetch flow, Table Presence | raw credential secret | Hash match; active; table and tenant enabled | Trusted tenant/table display context |
| `table_display.get_display_state` | TenantApp | tableId | Tenant Admin own tenant | Claim/credential status without raw secrets |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `table_display.provisioned` | Credential is issued/rotated | Audit, support state |
| `table_display.revoked` | Credential is revoked | Audit, QR fetch guards |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `claim_expired` | Provisioning claim is no longer usable. |
| `claim_consumed` | Claim was already exchanged. |
| `credential_revoked` | Display credential cannot fetch QR. |
| `wrong_table_or_tenant` | Credential-derived table context does not match allowed state. |
