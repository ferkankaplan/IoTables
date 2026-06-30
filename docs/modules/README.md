# Modules

IoTables is a modular monolith. The folders in this directory are bounded contexts, not app screens.

Apps define product semantics under `docs/apps`. Modules implement those app semantics through explicit context boundaries, internal modules, data ownership, and public interfaces.

## Context Folders

| Context | Folder | Purpose |
| --- | --- | --- |
| Platform | [platform](platform/README.md) | Platform tenant lifecycle and provisioning |
| Access | [access](access/README.md) | Human identity, login, app access, staff authorization, OTP |
| Tenant Setup | [tenant-setup](tenant-setup/README.md) | Tenant-owned operational configuration |
| Ordering | [ordering](ordering/README.md) | Customer presence, anonymous customer session, cart, order submission |
| Fulfillment | [fulfillment](fulfillment/README.md) | Preparation and service delivery execution |
| Settlement | [settlement](settlement/README.md) | Table session billing, payments, corrections, closure |
| Governance | [governance](governance/README.md) | Audit, policy evidence, and reliable external side effects |

## Shared Documents

| Document | Purpose |
| --- | --- |
| [module-map.md](module-map.md) | Context map, dependency direction, and module ownership |
| [_shared/module-template.md](_shared/module-template.md) | Standard format for module documents |
| [_shared/contract-format.md](_shared/contract-format.md) | Standard format for module command/query contracts |
| [_shared/api-contract-format.md](_shared/api-contract-format.md) | Standard format for module-owned HTTP API request/response contracts |
| [_shared/table-access-qr-flow.md](_shared/table-access-qr-flow.md) | End-to-end QR flow across Tenant Setup and Ordering |

## Rules

- Do not create a top-level module for every screen or entity.
- Put behavior under the context that owns the invariant.
- Keep app-specific UX under `docs/apps`.
- Keep cross-context mutation behind commands or events.
- Keep implementation packages aligned with this folder hierarchy.
