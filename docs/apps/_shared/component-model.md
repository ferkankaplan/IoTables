# Shared Component Model

This document defines the v1 product-level component model for all IoTables apps.

It is not a React component API and not a visual design system. It defines reusable UI responsibilities so each app package can describe its screens without inventing parallel patterns.

Source context:

- [semantic-source-rule.md](semantic-source-rule.md)
- [accessibility-responsive.md](accessibility-responsive.md)
- [copy-style.md](copy-style.md)
- [wireframe-rules.md](wireframe-rules.md)
- [cross-app-state-visibility.md](cross-app-state-visibility.md)
- [../platform/definition.md](../platform/definition.md)
- [../tenant/definition.md](../tenant/definition.md)
- [../customer/definition.md](../customer/definition.md)
- [../station-staff/definition.md](../station-staff/definition.md)
- [../service-staff/definition.md](../service-staff/definition.md)
- [../cashier/definition.md](../cashier/definition.md)

## Principles

- Components preserve app context instead of forcing unnecessary page navigation.
- A component owns one user-facing responsibility, not a database entity.
- Shared components must not weaken app-specific authority, visibility, or backend guard rules.
- UI state components must represent loading, empty, stale, unauthorized, pending, success, failure, and blocked states where the owning app can reach them.
- Components may be shared by shape and behavior, but app-specific copy, authority, and data visibility still come from app documents.

## Shared Component Layers

| Layer | Responsibility | Examples |
| --- | --- | --- |
| App Shell | Route-level layout, app identity, auth/session state, tenant/app context | Platform shell, tenant admin shell, cashier shell |
| Workspace | Primary durable page where the user keeps context | Hall workspace, cashier table board, station queue |
| Collection View | Repeated domain objects inside a workspace | Tenant list, table grid, menu list, queue list |
| Context Panel | Secondary object detail without leaving workspace | Table detail, session detail, item detail |
| Drawer / Bottom Sheet | Focused flow needing more space than a panel | Payment, product customization, cart review |
| Dialog | Short blocking decision or confirmation | OTP, TOTP, close session, void payment |
| State Banner / Inline State | Stale, unavailable, blocked, empty, or retry state | Fresh QR required, service disabled, check closed |
| Action Bar | Stable set of context-aware commands | Cart submit bar, queue item actions, payment actions |
| Status Indicator | Compact state label with accessible text | Tenant status, preparation status, balance state |

## Cross-App Components

### PlatformApp

| Component | Responsibility |
| --- | --- |
| PlatformLogin | Platform Owner username/password login state. |
| TenantHealthList | Active tenant list with lifecycle, DNS, provisioning, and safe health summaries. |
| TenantCreateDrawer | Tenant creation flow with required name, subdomain, GSM, and optional profile fields. |
| ProvisioningStatePanel | Provisioning, starter application, failure, and retry/recovery state. |
| DnsReadinessControl | Manual DNS readiness flag without DNS automation. |

### TenantApp

| Component | Responsibility |
| --- | --- |
| TenantPublicPage | Safe public tenant identity page with no operational internals. |
| TenantAdminShell | Authenticated tenant admin workspace shell. |
| HallWorkspace | Hall list and selected hall table grid in one context. |
| TableDetailPanel | Table edit, display provisioning, disable state, and runtime-safe blockers. |
| StationWorkspace | Station setup and station lifecycle management. |
| MenuWorkspace | Categories, products/services, variants, modifiers, availability, and station routing. |
| StaffWorkspace | Staff users, roles, station assignments, and hall assignments. |
| TenantSettingsWorkspace | Tenant profile fields, service tracking mode, and audit-visible settings. |

### CustomerApp

| Component | Responsibility |
| --- | --- |
| QrPresenceGate | Redeem QR, show retry state, and preserve cart when fresh presence is required. |
| TableContextHeader | Show customer-safe tenant/table context without exposing trusted IDs. |
| MenuCatalog | Category/product browsing with availability and image fallback states. |
| ProductDetailSheet | Product variant, modifier, quantity, note, and add-to-cart flow. |
| CartSheet | Editable cart, item-level stale states, and submit readiness. |
| CartActionBar | Stable cart count/total display and submit entry point. |
| OrderConfirmation | Accepted order, duplicate replay result, and return-to-menu action. |
| CustomerOrdersView | My Orders and Table Orders with mapped fulfillment states. |
| ReadOnlyBillSummary | Paid/remaining summary after fresh presence; no payment actions. |

### StationStaffApp

| Component | Responsibility |
| --- | --- |
| StationSelector | Select authorized station when more than one station is assigned. |
| StationQueueWorkspace | Touch-first station queue grouped by status and sorted by oldest work. |
| PreparationItemCard | Table, product, quantity, note, elapsed time, and current preparation state. |
| PreparationItemPanel | Detail view without leaving queue context. |
| PreparationActionBar | Start, mark ready, and cannot-prepare actions with pending state. |
| CannotPrepareDialog | Reason-required exception flow. |

### ServiceStaffApp

| Component | Responsibility |
| --- | --- |
| ServiceQueueWorkspace | Ready item queue scoped by authorized halls. |
| ServiceTableGroup | Ready/picked-up items grouped by physical table. |
| DeliveryItemPanel | Item detail without leaving queue context. |
| BulkDeliverySelectionBar | Same-table bulk selection, review, and submit state. |
| DeliveryActionBar | Picked-up and delivered actions with stale/unauthorized handling. |
| ServiceDisabledState | Service tracking disabled state with no delivery mutation controls. |

### CashierApp

| Component | Responsibility |
| --- | --- |
| CashierTableBoard | Halls, tables, active sessions, latest fulfillment, and balance summary. |
| SessionDetailPanel | Orders, items, Check/Adisyon, payments, corrections, and close eligibility. |
| PaymentDrawer | Partial/full payment recording with amount validation and pending state. |
| CorrectionDrawer | Allowed v1 correction flows with reason and target validation. |
| CloseSessionDialog | Explicit close action when remaining balance is zero. |
| PaymentHistoryWorkspace | Current business-day payment records and void states. |

## Reusable State Components

| Component | Required Use |
| --- | --- |
| LoadingState | Initial loads, panel loads, and action-pending states. |
| EmptyState | No tenants, halls, tables, queue items, cart items, sessions, or payments. |
| StaleState | Object changed while open; unsafe actions disabled until refresh. |
| UnauthorizedState | Authenticated but wrong role/scope. |
| TenantUnavailableState | Suspended/provisioning/unavailable tenant route. |
| RetryState | Network retry, QR retry, provider retry, or stale read retry. |
| ReasonField | Every reason-required destructive/audit action. |
| IdempotentReplayState | Duplicate submit returned original accepted result. |

## Anti-Patterns

- Do not create a primary page for every entity.
- Do not create standalone table management in v1; tables live inside HallWorkspace and TableDetailPanel.
- Do not use cards inside cards.
- Do not hide backend state uncertainty behind optimistic success copy.
- Do not create component variants that bypass app visibility rules.
- Do not expose internal IDs, token values, credential state, request hashes, or stack traces in customer-facing components.

## App Package Requirement

Each app UI package must map its wireframes to these shared component responsibilities. When an app needs a new component responsibility, first check whether it is a shared pattern, an app-specific component, or evidence that the app scenario needs revision.
