# App Flows

This folder defines IoTables v1 behavior across apps.

These documents sit between app-specific docs and module/schema/API design:

- app docs define each app's purpose and authority;
- app-flow docs define cross-app behavior and acceptance criteria;
- module docs, data model, and APIs must implement those behaviors without inventing parallel semantics.

## Documents

| Document | Purpose |
| --- | --- |
| [v1-end-to-end-flow.md](v1-end-to-end-flow.md) | Main tenant-to-order-to-settlement flow across all six apps |
| [v1-state-visibility-and-acceptance.md](v1-state-visibility-and-acceptance.md) | Cross-app state visibility matrix and v1 acceptance criteria |

## Rule

If a module, schema, or API decision conflicts with these flows, revise the app/app-flow docs first. Do not silently solve product behavior at the schema or API layer.
