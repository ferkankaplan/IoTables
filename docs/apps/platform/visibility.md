# PlatformApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | PlatformApp Visibility |
| --- | --- |
| Tenant `provisioning` | Full |
| Tenant `active` | Full |
| Tenant `suspended` | Full |
| Starter template applied | Full |
| Table display provisioned | Support/summary only |
| TableAccessToken redeemed | No normal view |
| CustomerOrderingSession active | No |
| Cart active | No |
| Order submitted | Health/audit summary only if exposed |
| Preparation `pending` | No |
| Preparation `preparing` | No |
| Preparation `ready` with service tracking enabled | No |
| Preparation `ready` with service tracking disabled | No |
| Preparation `cannot_prepare` | No |
| Delivery `picked_up` | No |
| Delivery `delivered` | No |
| Payment recorded | No direct runtime mutation |
| Payment voided | No direct runtime mutation |
| Cashier correction note | No normal view |
| Item void by cashier | No normal view |
| TableSession closed | Health/summary only if exposed |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
