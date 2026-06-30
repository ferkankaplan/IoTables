# Cross-App Master Scenario
### E2E-01: First Complete Table Visit

Happy path:

1. Platform Owner creates an active tenant.
2. Tenant Admin completes first login and reviews starter data.
3. Tenant Admin provisions the table display.
4. Customer scans the fresh table QR.
5. Customer builds and submits an order.
6. Station staff prepares assigned items.
7. Service staff delivers ready items when service tracking is enabled.
8. Cashier receives payment.
9. Cashier closes the TableSession.

Branches:

| Branch | Expected Result |
| --- | --- |
| Tenant provisioning fails | Tenant remains `provisioning_failed`; no runtime app should behave as active |
| Table display not provisioned | Customer cannot obtain a valid QR from that table |
| QR is expired/used/wrong-table | Customer must scan current QR again |
| Fresh presence expires before submit | Cart is preserved; customer must re-scan current QR |
| Product becomes unavailable before submit | Submit is rejected for affected item; cart remains editable |
| Duplicate order submit | Original idempotent result is returned; no duplicate order |
| Station reports `cannot_prepare` | Item remains billable until cashier correction; cashier sees exception |
| Service tracking disabled | ServiceStaffApp has no queue; `ready` becomes final tracked fulfillment |
| Partial payment only | TableSession remains open with remaining balance |
| Full payment but cashier does not close | TableSession remains open until explicit close |
| Close requested twice | Second request returns already-closed result without mutation |

Ownership:

- Platform: tenant lifecycle and provisioning.
- Tenant Setup: halls, tables, stations, menu, staff, display provisioning.
- Ordering: QR presence, customer session, cart, order submission.
- Fulfillment: preparation and service delivery.
- Settlement: Check/Adisyon, payments, corrections, closure.
- Governance: audit.
