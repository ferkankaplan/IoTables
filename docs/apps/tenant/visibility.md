# TenantApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | TenantApp Visibility |
| --- | --- |
| Tenant `provisioning` | Not available until tenant route resolves |
| Tenant `active` | Own tenant access |
| Tenant `suspended` | Block tenant admin runtime access unless recovery policy says otherwise |
| Starter template applied | Shows editable starter data |
| Table display provisioned | Full in table panel |
| TableAccessToken redeemed | No normal view |
| CustomerOrderingSession active | No |
| Cart active | No |
| Order submitted | No direct mutation |
| Preparation `pending` | No |
| Preparation `preparing` | No |
| Preparation `ready` with service tracking enabled | No |
| Preparation `ready` with service tracking disabled | Tenant setting explains mode |
| Preparation `cannot_prepare` | No direct runtime mutation |
| Delivery `picked_up` | No |
| Delivery `delivered` | No |
| Payment recorded | No |
| Payment voided | No |
| Cashier correction note | Audit if exposed |
| Item void by cashier | Audit if exposed |
| TableSession closed | No runtime mutation |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
