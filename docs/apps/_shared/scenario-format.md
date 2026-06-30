# Scenario Format

## Scope Rule
This file covers all v1-known branches for the six app surfaces:

- PlatformApp
- TenantApp
- CustomerApp
- StationStaffApp
- ServiceStaffApp
- CashierApp

When implementation discovers a new meaningful branch, it must be added here or explicitly rejected as out of scope before code, schema, or API behavior is finalized.

## Scenario Format
Each scenario uses this structure:

| Field | Meaning |
| --- | --- |
| Happy path | Expected normal path |
| Branches | Alternative or failure paths that must be handled |
| Result | State the system must reach |
| Ownership | App/context that owns the decision |
