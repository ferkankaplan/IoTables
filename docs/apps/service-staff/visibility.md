# ServiceStaffApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | ServiceStaffApp Visibility |
| --- | --- |
| Tenant `provisioning` | Not available |
| Tenant `active` | Staff access allowed if enabled |
| Tenant `suspended` | Block |
| Starter template applied | Indirect through service users |
| Table display provisioned | None |
| TableAccessToken redeemed | None |
| CustomerOrderingSession active | No |
| Cart active | No |
| Order submitted | Later ready items appear |
| Preparation `pending` | Not yet visible |
| Preparation `preparing` | Not yet visible |
| Preparation `ready` with service tracking enabled | Ready queue |
| Preparation `ready` with service tracking disabled | No queue |
| Preparation `cannot_prepare` | Not serviceable |
| Delivery `picked_up` | Visible if authorized hall |
| Delivery `delivered` | Delivered/recent state |
| Payment recorded | No |
| Payment voided | No |
| Cashier correction note | No |
| Item void by cashier | Not serviceable |
| TableSession closed | Closed items no longer mutable |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
