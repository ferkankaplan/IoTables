# Module Contracts: Table Presence

Source module: [table-presence.md](table-presence.md)

## Commands

| Command | Caller | Input | Guards / Validation | Transaction / Idempotency | Result |
| --- | --- | --- | --- | --- | --- |
| `table_presence.issue_current_qr_token` | ESP32 display QR fetch | authenticated display context | Display credential authenticated by Table Display Provisioning; tenant/table enabled | Create or return current short-lived token under table/display lock; raw token returned only in QR payload | QR token payload with expiry |
| `table_presence.redeem_token` | CustomerApp | raw QR token, optional existing customer session cookie | Token hash exists, unexpired, unconsumed; table/tenant enabled | Atomic consume; refresh compatible CustomerOrderingSession presence; rotate next token on subsequent display fetch | CustomerOrderingSession cookie/update and fresh presence window |
| `table_presence.expire_old_tokens` | Internal retention job | cutoff | Internal operation; no active token mutation that breaks current display flow | Mark/purge according to retention policy | Cleanup result |

## Queries

| Query | Caller | Input / Scope | Guards | Result |
| --- | --- | --- | --- | --- |
| `table_presence.require_fresh_presence` | Customer Ordering, Settlement read guards | customerOrderingSessionId, tableId | Presence valid until now; session/table compatible | Success or fresh QR required |
| `table_presence.get_presence_state` | CustomerApp | customer session cookie | Session owner only; no trusted table IDs from client | Presence expiry and table context |

## Consumed Contracts

| Contract | Purpose |
| --- | --- |
| `table_display.authenticate_credential` | Resolve trusted tenant/table for QR fetch. |
| `customer_ordering.attach_or_refresh_session` | Refresh the anonymous browser session after QR redemption. |

## Events

| Event | Emitted When | Consumers |
| --- | --- | --- |
| `table_access_token.redeemed` | QR token is successfully consumed | Customer Ordering, audit/security metrics |

## Failure Outcomes

| Failure | Meaning |
| --- | --- |
| `token_expired` | QR token lifetime ended. |
| `token_consumed` | QR token already used. |
| `fresh_presence_required` | Customer must scan a current table QR before protected action. |
| `display_not_authenticated` | QR issuance did not come from active table display credential. |
