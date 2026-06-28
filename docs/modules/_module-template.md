# Module: <Module Name>

## Purpose

What business capability does this module own?

## Context

| Field | Value |
| --- | --- |
| Parent bounded context | Platform / Access / Tenant Setup / Ordering / Fulfillment / Settlement / Governance |
| Module type | context module / internal module / cross-cutting support |

## Ownership

| Owned Concept | Type | Authority |
| --- | --- | --- |
| Example | Entity / Value / State / Event | create, read, update, transition, publish |

## Not Owned

- Concepts or workflows this module must not own.

## Users and App Access

Which apps and users can use this module, and how far can they go?

| App / Actor | Access | Limits |
| --- | --- | --- |
| ExampleApp | read / write / transition | Tenant-scoped only |

## Public Interface

How other modules interact with this module.

| Interface | Purpose | Consumers |
| --- | --- | --- |
| Command / Query / Event / API | What it does | Who uses it |

## Internal Rules

- Domain invariants and business rules.

## Operational Safety

- Idempotency requirements.
- Authorization guards.
- Transaction boundaries.
- Rollback/recovery behavior.
- Database constraints.

## Data Model

| Model / Table | Purpose | Notes |
| --- | --- | --- |
| Example | Stores module-owned data | Important constraints |

## App Surfaces

| App | Usage |
| --- | --- |
| ExampleApp | How the app uses this module |

## Future Service Boundary

If this module is extracted later, what is the boundary?

- Own data:
- Own APIs:
- Published events:
- Consumed events:
- Must not leak:

## Open Questions

- Questions that block implementation or need product decisions.
