# Accessibility and Responsive UI Rules

This document defines shared current release accessibility and responsive behavior for all six apps.

Source context:

- [semantic-source-rule.md](semantic-source-rule.md)
- [component-model.md](component-model.md)
- [wireframe-rules.md](wireframe-rules.md)
- [canonical-end-to-end.md](canonical-end-to-end.md)
- [cross-app-state-visibility.md](cross-app-state-visibility.md)
- [../../api/auth.md](../../api/auth.md)
- [../../api/errors.md](../../api/errors.md)
- [../../security/threat-model.md](../../security/threat-model.md)

Baseline target: WCAG 2.2 AA. Product rules below may be stricter where restaurant operations need faster, safer touch interaction.

## Shared Principles

- Keep users in context. Prefer panels, drawers, dialogs, bottom sheets, and inline editing over unnecessary navigation.
- Use the shared component model to keep repeated layout responsibilities consistent across app packages.
- CustomerApp is mobile-first and customer-polished.
- StationStaffApp, ServiceStaffApp, and CashierApp are touch-first operational tools.
- TenantApp and PlatformApp are dense admin tools, but must still work on tablet and narrow desktop.
- Frontend visibility is never authorization. Disabled/hidden controls are UX only; backend guards remain mandatory.
- Do not expose internal security terms such as token, hash, credential, idempotency, or session to customers.

## Responsive Baseline

| Viewport / Surface | Required Behavior |
| --- | --- |
| Small mobile | Single-column layout; bottom sheets or full-height drawers for detail; primary action fixed only when it does not cover content. |
| Large mobile / tablet | Two-column or split layouts allowed; active context remains visible when a panel opens. |
| Desktop | Stable workspace with contextual right panels, drawers, or dialogs; avoid deep page hopping for secondary objects. |
| Operational tablets | Large hit areas, persistent selected context, minimal scrolling during repeated actions. |

Rules:

- Layout must not depend on viewport-width font scaling.
- Text must not overlap, clip, or require horizontal scrolling in normal Turkish copy.
- Boards, queues, menus, and toolbars need stable dimensions so hover, loading, count, and status changes do not shift the layout.
- Cards are for repeated items, modals, and genuinely framed tools. Do not put cards inside cards.
- Tables remain managed inside hall context; table detail uses contextual panels unless a later workflow explicitly changes that.

## Touch and Pointer Targets

| Control Type | Minimum Target |
| --- | --- |
| Customer primary actions | 48 x 48 CSS px |
| Operational repeated actions | 48 x 48 CSS px |
| Admin primary/secondary buttons | 40 x 40 CSS px |
| Icon-only buttons | 40 x 40 CSS px, with accessible name and tooltip when meaning is not obvious |
| Dense inline text links | May be smaller only when a nearby equivalent control meets the target rule |

Spacing:

- Adjacent destructive and primary actions must not be so close that accidental taps are likely.
- Operational queue actions such as `start`, `ready`, `picked_up`, `delivered`, payment, void, and close need extra spacing from destructive alternatives.
- Disabled pending buttons must remain visible and stable while an operation is in progress.

## Keyboard and Focus

- Every interactive element must be reachable by keyboard unless it is a purely duplicated pointer affordance with an equivalent keyboard path.
- Focus order follows visual order and current context.
- Opening a drawer, dialog, or bottom sheet moves focus into it.
- Closing a drawer, dialog, or bottom sheet restores focus to the opener when possible.
- Escape closes non-destructive overlays. Destructive confirmation dialogs may require explicit cancel/confirm buttons.
- Focus indicators must be visible and not hidden by sticky headers, bottom bars, or scroll containers.
- Keyboard users must be able to complete payment, correction, QR retry, cart submit, station transition, service delivery, and tenant setup flows.

## Visual Contrast and State

- Normal text targets WCAG AA contrast.
- Important status, warning, error, success, and destructive states must not rely on color alone.
- Use icons plus text where color could be ambiguous.
- Cashier payment/void, station `cannot_prepare`, service delivery, and customer QR retry states need explicit text labels.
- Loading, empty, stale, unauthorized, expired, disabled, and blocked states must be visually distinct.

## Forms and Validation

- Labels are always visible or programmatically associated. Placeholder text is not a label.
- Required fields must be clear before submit.
- Validation errors appear near the field and in a safe summary when the flow is complex.
- Error copy uses app-facing language and does not expose stack traces, SQL, raw provider responses, token values, hashes, or internal paths.
- Reason-required flows focus the reason field when missing:
  - station `cannot_prepare`;
  - payment void;
  - cashier correction;
  - tenant disable/revoke actions where reason is required.

## Contextual Overlays

| Overlay | Use |
| --- | --- |
| Right panel | Admin/cashier detail while keeping board/list context. |
| Drawer | Payment, correction, setup, or detail flows that need more space but not a new page. |
| Dialog | Confirmation, destructive action, short OTP/TOTP prompt, or blocking decision. |
| Bottom sheet | Customer product detail, QR re-verification, cart review, and mobile detail flows. |

Rules:

- Overlay title must identify the object and state.
- Overlay actions stay within the overlay and do not move the user to an unrelated page.
- Background context remains visible when useful, but must not be keyboard-focusable while a modal dialog is active.
- Nested cards inside overlays are avoided unless representing repeated child items.

## Loading, Empty, Stale, and Error States

Every app package must document:

- initial loading;
- empty data;
- partial data unavailable;
- stale object while a panel is open;
- auth/session expired;
- wrong role/scope;
- tenant unavailable/suspended;
- network retry;
- duplicate submit or operation already processed;
- destructive action blocked.

State changes must preserve context. For example, a stale table panel refreshes or disables unsafe actions instead of dumping the user to a generic dashboard.

## App-Specific Baselines

| App | Baseline |
| --- | --- |
| PlatformApp | Quiet dense admin UI; tenant health and provisioning states must be scannable. |
| TenantApp | Few stable pages; hall/table, station, menu, staff, and settings use contextual panels. |
| CustomerApp | Mobile-first menu/cart/order UX; table context visible; QR retry feels like table confirmation, not technical error. |
| StationStaffApp | Touch-first queue; large actions; item detail panel; strong stale/unauthorized state handling. |
| ServiceStaffApp | Touch-first table-grouped ready queue; bulk delivery selection must be stable and reversible before submit. |
| CashierApp | Table board plus session detail panel; payment/correction/close flows in drawers/dialogs without losing table context. |

## Verification Checklist

Each app UI package must include checks for:

- wireframes map primary regions to shared component responsibilities;
- no overlapping text or controls at small mobile, tablet, and desktop widths;
- all primary workflows keyboard reachable;
- visible focus state;
- touch targets meet this document;
- loading/empty/error/stale states documented;
- disabled controls are paired with backend guard expectations;
- customer copy avoids internal security jargon;
- sensitive data is not displayed outside allowed visibility rules.

## References

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WCAG 2.2 Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
- [WCAG 2.2 Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)
