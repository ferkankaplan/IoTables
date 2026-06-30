# CashierApp Visibility

This document is an app-specific projection of the shared cross-app visibility matrix.

| State / Event | CashierApp Visibility |
| --- | --- |
| Tenant `provisioning` | Not available |
| Tenant `active` | Cashier access allowed |
| Tenant `suspended` | Block |
| Starter template applied | Indirect through cashier user |
| Table display provisioned | Table state only |
| TableAccessToken redeemed | No normal view |
| CustomerOrderingSession active | No |
| Cart active | No |
| Order submitted | Session/order panel updates |
| Preparation `pending` | Visible in session item status |
| Preparation `preparing` | Visible in session item status |
| Preparation `ready` with service tracking enabled | Visible in session item status |
| Preparation `ready` with service tracking disabled | Visible as final tracked fulfillment |
| Preparation `cannot_prepare` | Visible exception requiring cashier attention |
| Delivery `picked_up` | Visible in session item status |
| Delivery `delivered` | Visible in session item status |
| Payment recorded | Full |
| Payment voided | Full with reason |
| Cashier correction note | Full |
| Item void by cashier | Full with reason |
| TableSession closed | Full |

See also: [shared cross-app visibility](../_shared/cross-app-state-visibility.md).
