# Wireframe Rules

This document defines how v1 wireframe documents should be written for IoTables apps.

Wireframes are app-level semantic documents. They describe user workflow, layout responsibility, state, and interaction boundaries. They do not define React implementation details, CSS tokens, or database/API behavior.

Source context:

- [semantic-source-rule.md](semantic-source-rule.md)
- [component-model.md](component-model.md)
- [accessibility-responsive.md](accessibility-responsive.md)
- [copy-style.md](copy-style.md)
- [cross-app-state-visibility.md](cross-app-state-visibility.md)
- [scenario-format.md](scenario-format.md)

## Required Structure

Every app `wireframes.md` must include:

1. Primary workspaces and durable URLs.
2. Contextual panels, drawers, dialogs, and bottom sheets.
3. Mobile, tablet, and desktop layout notes.
4. Loading, empty, stale, unauthorized, blocked, and error states.
5. Pending/duplicate-submit behavior for mutating actions.
6. Accessibility notes for focus, keyboard, touch targets, and visible state.
7. Data visibility boundaries, linked to app `visibility.md`.
8. Out-of-scope UI that must not appear in v1.

## Page and Overlay Rules

Use the fewest durable pages that preserve a clear working context.

| UI Shape | Use When |
| --- | --- |
| Durable page | The workflow has a distinct primary context or needs a durable URL. |
| Right panel | Editing or inspecting a secondary object while keeping a board/list visible. |
| Drawer | Focused flow with multiple fields or review steps. |
| Dialog | Short confirmation, destructive action, OTP/TOTP, or blocking choice. |
| Bottom sheet | Mobile product detail, cart review, QR retry, or compact customer detail flow. |
| Inline edit | Small reversible field edit that does not need a separate flow. |

Rules:

- Do not split tightly owned concepts into separate primary screens.
- Tables are managed inside Hall Management; table detail opens in context.
- Session detail opens inside Cashier Workspace unless a durable history/reporting workspace is explicitly defined.
- Station and service item details open in queue context.
- Customer product detail opens from the menu as a panel or bottom sheet.

## Wireframe State Matrix

Every major surface must document these states:

| State | Required Description |
| --- | --- |
| Loading | What remains stable while data loads. |
| Empty | What natural next action appears if the actor can act. |
| Stale | What disables, refreshes, or asks for retry when state changes. |
| Unauthorized | How wrong role/scope appears without leaking hidden records. |
| Tenant unavailable | What the app shows for suspended, provisioning, or missing tenant. |
| Pending action | Which controls disable and what remains visible. |
| Duplicate/replay | How original accepted result is shown without creating a new record. |
| Validation error | Field-level and summary behavior. |
| Destructive blocked | Why the action is unavailable and where the user can recover. |

## Responsive Rules

| App | Mobile | Tablet | Desktop |
| --- | --- | --- | --- |
| PlatformApp | Basic admin fallback; tenant list remains readable | Dense list with create drawer | Tenant health table/list plus detail/recovery panel |
| TenantApp | Single workspace stack; panels become full-height drawers | Hall/menu/staff split views | Stable workspaces with right panels |
| CustomerApp | Primary target; bottom sheets and fixed safe action bar | Menu/detail/cart split when useful | Wider menu with cart/detail side context |
| StationStaffApp | Touch queue first; no dense table-only layout | Queue plus item drawer | Queue groups with detail panel |
| ServiceStaffApp | Touch table groups; stable bulk selection | Table groups plus detail drawer | Queue workspace with detail panel |
| CashierApp | Usable fallback; table board may stack above session detail | Table board plus session drawer | Board and session panel side by side |

No layout may depend on viewport-width font scaling. Text must wrap or use stable responsive containers.

## Component Mapping

Wireframes must map visible regions to [component-model.md](component-model.md):

| Wireframe Region | Must Identify |
| --- | --- |
| Shell/header/nav | App context, auth/session state, tenant/table context where visible |
| Main workspace | Owning app workflow and durable URL |
| Collection/board/queue | Sort/group rules and empty/loading states |
| Detail panel/drawer | Object identity, safe fields, stale behavior |
| Action area | Mutating commands, pending state, backend guard expectation |
| Status labels | Domain state mapping and allowed visibility |
| Error/retry area | App-facing copy and next action |

## Copy and Visibility Rules

- Use user-facing Turkish copy from [copy-style.md](copy-style.md).
- Do not put implementation terms in customer or operational UI.
- Do not show data outside [cross-app-state-visibility.md](cross-app-state-visibility.md).
- Disabled controls must not imply authorization; backend guards remain required.
- CustomerApp must not expose payment mutation, cancellation, refund, discount, session closure, setup, staff, token, or credential UI.
- TenantApp must not expose live order/payment mutation controls.
- CashierApp must not expose tenant setup controls.

## Interaction Safety

For every mutating action, wireframes must show:

- disabled pending control;
- clear pending state;
- success state only after backend acceptance;
- duplicate/replay result if applicable;
- stale-state recovery;
- reason field where required;
- confirmation when destructive, audit-affecting, or easy to trigger accidentally.

## Verification

Before an app wireframe is accepted:

- every app scenario has a visible path or explicit non-UI handling;
- every app `ui-states.md` state appears in a surface;
- every mutating action has pending, blocked, stale, and failure states;
- every surface preserves context unless a durable page is justified;
- every visible status is allowed by the app visibility document;
- no v1 out-of-scope control appears.
