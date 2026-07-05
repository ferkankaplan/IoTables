# StationStaffApp End-to-End Role

This document extracts the parts of the shared current release end-to-end flow where this app participates.

See the full shared flow: [../_shared/master-end-to-end.md](../_shared/master-end-to-end.md).

### 6. Station Staff Prepares Items
1. Station staff logs into StationStaffApp.
2. If assigned to one station, the station queue opens directly.
3. If assigned to multiple stations, station selection opens first.
4. Staff sees authorized station items grouped by preparation status and sorted oldest first.
5. Staff moves items from `pending` to `preparing`.
6. Staff marks prepared items `ready`, or marks impossible items `cannot_prepare` with a reason.

Acceptance criteria:

- Station staff cannot see or update unauthorized stations.
- Status transitions validate current state server-side.
- `cannot_prepare` requires a reason and actor.
- `cannot_prepare` does not cancel, refund, discount, reprice, close session, or remove billable records.
- CashierApp can see `cannot_prepare`.
