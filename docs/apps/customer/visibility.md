# CustomerApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | CustomerApp Visibility |
| --- | --- |
| Tenant `provisioning` | Not available |
| Tenant `active` | Public/customer access allowed |
| Tenant `suspended` | Show unavailable |
| Starter template applied | Indirect through menu/table availability |
| Table display provisioned | Indirect through QR availability |
| TableAccessToken redeemed | Creates/refreshes session and presence |
| CustomerOrderingSession active | Own browser session |
| Cart active | Full for owning browser |
| Order submitted | Confirmation, My Orders, Table Orders |
| Preparation `pending` | `Hazırlanıyor` |
| Preparation `preparing` | `Hazırlanıyor` |
| Preparation `ready` with service tracking enabled | `Hazırlanıyor` |
| Preparation `ready` with service tracking disabled | `Teslim edildi` |
| Preparation `cannot_prepare` | Still bill-visible unless cashier corrects |
| Delivery `picked_up` | `Hazırlanıyor` |
| Delivery `delivered` | `Teslim edildi` |
| Payment recorded | Read-only bill/balance update after fresh presence |
| Payment voided | Read-only bill/balance update after fresh presence |
| Cashier correction note | No |
| Item void by cashier | Table bill/order state updates read-only |
| TableSession closed | Requires fresh QR for any new order context |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
