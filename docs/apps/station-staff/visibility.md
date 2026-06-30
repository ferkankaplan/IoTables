# StationStaffApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | StationStaffApp Visibility |
| --- | --- |
| Tenant `provisioning` | Not available |
| Tenant `active` | Staff access allowed |
| Tenant `suspended` | Block |
| Starter template applied | Indirect through station queues |
| Table display provisioned | None |
| TableAccessToken redeemed | None |
| CustomerOrderingSession active | No |
| Cart active | No |
| Order submitted | Assigned items appear |
| Preparation `pending` | Visible if assigned station |
| Preparation `preparing` | Visible if assigned station |
| Preparation `ready` with service tracking enabled | Ready/recent state |
| Preparation `ready` with service tracking disabled | Ready/final state |
| Preparation `cannot_prepare` | Visible exception |
| Delivery `picked_up` | May leave active ready queue |
| Delivery `delivered` | Recent/history only |
| Payment recorded | No |
| Payment voided | No |
| Cashier correction note | No |
| Item void by cashier | Removed/marked outside active prep if still pending/cannot_prepare |
| TableSession closed | Closed items no longer mutable |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
