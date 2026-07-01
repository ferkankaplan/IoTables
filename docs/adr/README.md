# Architecture Decision Records

This folder records locked architecture decisions for IoTables v1.

ADR files do not replace app, module, data, API, or test documents. They explain why a foundational decision is locked and which source documents must stay synchronized with it.

## Decisions

| ADR | Decision |
| --- | --- |
| [modular-monolith.md](modular-monolith.md) | Build IoTables as a modular monolith with bounded contexts. |
| [six-app-semantic-source.md](six-app-semantic-source.md) | Treat the six apps as the semantic source for lower layers. |
| [qr-presence-session-model.md](qr-presence-session-model.md) | Separate table display credentials, QR presence, CustomerOrderingSession, and TableSession. |
| [shared-schema-tenancy.md](shared-schema-tenancy.md) | Use shared PostgreSQL tables with tenant-owned rows in v1. |
| [reliable-side-effects-outbox.md](reliable-side-effects-outbox.md) | Use durable outbox and attempt records for non-transactional side effects. |

## Rules

- If an ADR conflicts with an app scenario, repair the app scenario first, then update the ADR and downstream layers.
- If a module, data model, API, migration, or test contradicts a locked ADR, repair the downstream document unless the product decision has changed.
- ADRs are semantic source documents and are included in `docs/semantic/index.jsonl`.
