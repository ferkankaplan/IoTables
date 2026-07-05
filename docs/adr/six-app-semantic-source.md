# ADR: Six Apps as Semantic Source

## Status

Accepted for the current release.

## Context

IoTables is defined by six product surfaces:

- PlatformApp
- TenantApp
- CustomerApp
- StationStaffApp
- ServiceStaffApp
- CashierApp

The internal architecture exists to implement these apps, not to invent product behavior independently at the module, schema, API, or test layer.

Sources:

- [../apps/README.md](../apps/README.md)
- [../apps/_shared/semantic-source-rule.md](../apps/_shared/semantic-source-rule.md)
- [../semantic/source-policy.md](../semantic/source-policy.md)
- [../modules/module-map.md](../modules/module-map.md)

## Decision

The six apps are the semantic foundation of IoTables the current release.

The required derivation direction is:

1. App scenario
2. App workflow and branch behavior
3. App UI state, permission, and visibility rules
4. Module responsibility and ownership boundary
5. Module command, event, invariant, and integration contract
6. Data model, transaction, rollback, and retention rule
7. API request, response, authorization, idempotency, and error contract
8. Test scenario and acceptance criteria
9. Implementation code and runtime configuration
10. Generated or derived artifacts such as semantic index records

## Consequences

- Module design cannot be treated as the first product source.
- If a module contract conflicts with an app scenario, update the app decision first, then reshape the module.
- If an API or schema field cannot be traced to an app scenario or module invariant, it is either undocumented or out of scope.
- Semantic index retrieval must prefer app and ownership metadata before broad similarity.
- Tests must prove app-visible behavior and lower-layer invariants rather than merely exercising implementation details.

## Synchronization Points

- App definitions and scenarios: [../apps](../apps/README.md)
- Semantic hierarchy: [../semantic/source-policy.md](../semantic/source-policy.md)
- Module map: [../modules/module-map.md](../modules/module-map.md)
- Semantic index usage: [../semantic/README.md](../semantic/README.md)

## Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Entity-first design | It tends to create tables and APIs before user scenarios are understood. |
| API-first product semantics | It can harden accidental endpoint shapes into product truth. |
| Roadmap/checklist as source truth | Planning files do not define behavior and must not drive semantic retrieval. |

## Review Trigger

Review this ADR only if the product surface changes from the six-app model. Adding a new document, module, or endpoint is not enough to change the semantic foundation.
