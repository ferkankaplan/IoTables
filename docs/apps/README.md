# Apps

This folder is the product-semantic source for IoTables v1.

Each app has its own folder. Shared cross-app rules live under `_shared` to avoid duplicated matrices and global decisions.

## App Folders

| App | Folder |
| --- | --- |
| [PlatformApp](platform/README.md) | `platform/` |
| [TenantApp](tenant/README.md) | `tenant/` |
| [CustomerApp](customer/README.md) | `customer/` |
| [StationStaffApp](station-staff/README.md) | `station-staff/` |
| [ServiceStaffApp](service-staff/README.md) | `service-staff/` |
| [CashierApp](cashier/README.md) | `cashier/` |

## Shared Documents

| Document | Purpose |
| --- | --- |
| [_shared/semantic-source-rule.md](_shared/semantic-source-rule.md) | Rule that app docs govern module/schema/API semantics |
| [_shared/master-end-to-end.md](_shared/master-end-to-end.md) | Shared tenant-to-order-to-settlement flow |
| [_shared/master-scenario.md](_shared/master-scenario.md) | Cross-app master happy path and branch scenario |
| [_shared/branch-coverage-checklist.md](_shared/branch-coverage-checklist.md) | Required branch coverage before API contracts |
| [_shared/scenario-format.md](_shared/scenario-format.md) | Format and scope rule for app scenarios |
| [_shared/cross-app-state-visibility.md](_shared/cross-app-state-visibility.md) | Full cross-app state visibility matrix |
| [_shared/v1-out-of-scope.md](_shared/v1-out-of-scope.md) | Global out-of-scope scenario requests |

## Per-App Document Set

Each app folder contains:

- `definition.md`
- `semantic-source.md`
- `end-to-end.md`
- `scenarios.md`
- `visibility.md`
- `acceptance-criteria.md`
- `ui-states.md`
- `out-of-scope.md`

Do not add new app behavior only to modules, schema, or APIs. Merge behavior here first.
