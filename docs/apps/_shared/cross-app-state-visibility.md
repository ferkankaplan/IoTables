# Cross-App State Visibility
| State / Event | PlatformApp | TenantApp | CustomerApp | StationStaffApp | ServiceStaffApp | CashierApp |
| --- | --- | --- | --- | --- | --- | --- |
| Tenant `provisioning` | Full | Not available until tenant route resolves | Not available | Not available | Not available | Not available |
| Tenant `active` | Full | Own tenant access | Public/customer access allowed | Staff access allowed | Staff access allowed if enabled | Cashier access allowed |
| Tenant `suspended` | Full | Block tenant admin runtime access unless recovery policy says otherwise | Show unavailable | Block | Block | Block |
| Starter template applied | Full | Shows editable starter data | Indirect through menu/table availability | Indirect through station queues | Indirect through service users | Indirect through cashier user |
| Table display provisioned | Support/summary only | Full in table panel | Indirect through QR availability | None | None | Table state only |
| TableAccessToken redeemed | No normal view | No normal view | Creates/refreshes session and presence | None | None | No normal view |
| CustomerOrderingSession active | No | No | Own browser session | No | No | No |
| Cart active | No | No | Full for owning browser | No | No | No |
| Order submitted | Health/audit summary only if exposed | No direct mutation | Confirmation, My Orders, Table Orders | Assigned items appear | Later ready items appear | Session/order panel updates |
| Preparation `pending` | No | No | `Hazırlanıyor` | Visible if assigned station | Not yet visible | Visible in session item status |
| Preparation `preparing` | No | No | `Hazırlanıyor` | Visible if assigned station | Not yet visible | Visible in session item status |
| Preparation `ready` with service tracking enabled | No | No | `Hazırlanıyor` | Ready/recent state | Ready queue | Visible in session item status |
| Preparation `ready` with service tracking disabled | No | Tenant setting explains mode | `Teslim edildi` | Ready/final state | No queue | Visible as final tracked fulfillment |
| Preparation `cannot_prepare` | No | No direct runtime mutation | Still bill-visible unless cashier corrects | Visible exception | Not serviceable | Visible exception requiring cashier attention |
| Delivery `picked_up` | No | No | `Hazırlanıyor` | May leave active ready queue | Visible if authorized hall | Visible in session item status |
| Delivery `delivered` | No | No | `Teslim edildi` | Recent/history only | Delivered/recent state | Visible in session item status |
| Payment recorded | No direct runtime mutation | No | Read-only bill/balance update after fresh presence | No | No | Full |
| Payment voided | No direct runtime mutation | No | Read-only bill/balance update after fresh presence | No | No | Full with reason |
| Cashier correction note | No normal view | Audit if exposed | No | No | No | Full |
| Item void by cashier | No normal view | Audit if exposed | Table bill/order state updates read-only | Removed/marked outside active prep if still pending/cannot_prepare | Not serviceable | Full with reason |
| TableSession closed | Health/summary only if exposed | No runtime mutation | Requires fresh QR for any new order context | Closed items no longer mutable | Closed items no longer mutable | Full |
