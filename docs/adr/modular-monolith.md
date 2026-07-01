# ADR: Modular Monolith with Bounded Contexts

## Status

Accepted for v1.

## Context

IoTables has six user-facing apps, but those apps are not the same thing as internal modules. The product needs coherent boundaries for tenant provisioning, access control, tenant setup, ordering, fulfillment, settlement, and governance without the deployment and operational cost of separate services in v1.

The current module map already defines IoTables as a modular monolith where apps call context/module interfaces and internal state stays behind the owning boundary.

Sources:

- [../modules/module-map.md](../modules/module-map.md)
- [../modules/README.md](../modules/README.md)
- [../semantic/source-policy.md](../semantic/source-policy.md)

## Decision

IoTables v1 is a modular monolith.

Bounded contexts are the primary architecture units:

- Platform
- Access
- Tenant Setup
- Ordering
- Fulfillment
- Settlement
- Governance

Internal modules live inside these contexts. They expose explicit commands, queries, events, and API contracts. Apps must not mutate another context's owned data directly.

## Consequences

- The repository structure, package boundaries, migrations, tests, and API contracts must follow the bounded context map.
- A new capability must merge into the owning context instead of creating a parallel top-level module.
- Cross-context mutation must go through commands or events.
- Contexts may share a deployment unit and database in v1, but they must not share ownership of aggregates.
- Future service extraction, if ever needed, must preserve the same public context interfaces.

## Synchronization Points

- Context ownership: [../modules/module-map.md](../modules/module-map.md)
- Module contracts: [../modules](../modules/README.md)
- Data ownership: [../data-model.md](../data-model.md)
- Schema ownership: [../database/schema.md](../database/schema.md)
- API contracts: [../api/README.md](../api/README.md)

## Rejected Alternatives

| Alternative | Reason Rejected |
| --- | --- |
| Screen-per-module architecture | It duplicates business rules across apps and breaks encapsulation. |
| Early microservices | It adds deployment, consistency, and integration cost before boundaries are proven in code. |
| Flat utility modules | It hides ownership and makes invariants hard to enforce. |

## Review Trigger

Review this ADR only if a bounded context repeatedly needs independent deployment, independent scaling, or a materially different data lifecycle. Do not split services merely because a file or entity count grows.
