# V1 Architecture Backlog

This backlog collects the architecture findings from IoTables docs review and external restaurant/POS product research.

It is not a feature wishlist. A finding appears here only if it affects one of these before implementation:

- database schema,
- public API contracts,
- bounded context ownership,
- v1 scope clarity,
- financial/legal correctness,
- security or concurrency behavior.

## Priority Rules

| Priority | Meaning |
| --- | --- |
| P0 | Must be decided before backend schema and API implementation |
| P1 | Must be decided before first end-to-end v1 flows |
| P2 | Must be explicitly in or out of v1 scope before UI implementation |
| P3 | Important later; document now, implement after v1 unless needed |

## P0: Schema and Boundary Blockers

### 0. Close app-level scenario gaps first

Status:

- The six app docs are the semantic source for modules, contexts, schemas, and APIs.
- App-level v1 scenario gaps are closed at documentation level.
- Deeper module and data-model updates should now merge into these app decisions instead of introducing parallel concepts.

Locked app decisions:

- CustomerApp has no separate price preview or customer price-confirmation step in v1; backend pricing still remains authoritative.
- CustomerApp cannot receive customer payment or start pay-at-table flows in v1.
- CashierApp uses one operational Check/Adisyon per active TableSession in v1.
- CashierApp does not support split checks, item/person-based split, item move, merge checks, fiscal receipt issuance, or customer payment in v1.
- TenantApp does not configure fiscal/e-Adisyon/ÖKC, kitchen printers, receipt printers, cash drawers, or hardware integrations in v1.
- TenantApp does not configure waiter-entered orders, package service, courier, pickup, delivery, counter sale, stock/recipe, or multi-location operations in v1.
- PlatformApp tenant creation makes v1 scope visible: single location, dine-in QR ordering, manual DNS, no fiscal integration, no external payment provider, no offline POS.
- StationStaffApp supports `cannot_prepare` as an operational exception with a required reason; it does not cancel, refund, discount, or remove billable records.
- ServiceStaffApp is enabled by default for the cafe starter template but can be disabled per tenant. When disabled, `PreparationItem.ready` is the final tracked fulfillment state.

Why:

The architecture is app-first. PlatformApp, TenantApp, CustomerApp, StationStaffApp, ServiceStaffApp, and CashierApp define the semantic foundation. Modules exist to implement those app scenarios, not to create independent domain complexity.

Output:

- Update module docs and data model from the locked app decisions.

### 1. Lock v1 operating scope

App-level decision:

- `tenant = one restaurant/location` in v1.
- `OrderChannel = dine_in_qr` only in v1.
- CustomerApp cannot receive payments in v1.
- CashierApp is the only payment/close-session surface in v1.
- No waiter-entered orders in v1.
- No pickup, package service, courier, phone order, online marketplace, or counter-sale channel in v1.
- No offline-first local POS mode in v1; server connection is required.
- Product/service routes to one station in v1.

Why:

Square, Toast, Olo, Simpra, Menulux, GoPOS, and similar systems model locations and channels as first-class capabilities. If IoTables v1 is narrower, the narrow scope must be explicit before schemas and URLs harden.

Output:

- Add explicit v1 scope section to app/module docs.
- Add `orderChannel` to order data model with only `dine_in_qr` enabled.
- Keep multi-location and non-QR channels out of v1 migrations.

### 2. Implement Check / Adisyon model in schema and module docs

App-level decision:

- V1 uses exactly one operational Check/Adisyon per active TableSession.
- Split checks, merge checks, item/person-based payment splitting, and moving items between checks are out of v1.

Why:

Toast, TouchBistro, SambaPOS, DİA, GoPOS, OxyMenu, and local e-Adisyon workflows treat check/adisyon behavior as central. Without a deliberate model, billing, fiscal documents, split bill, item cancellation, and corrections will be bolted onto TableSession later.

Output:

- Update `data-model.md`.
- Update `table-session-billing.md`.
- Update `payments.md`.
- Update CashierApp docs.

### 3. Add pricing and adjustment contract

Decision needed:

- Do not add a separate order price preview/quote endpoint in v1.
- Add `PriceAdjustment` model for tax, discount, service charge, campaign, and future correction adjustments.
- Keep frontend totals informational only.
- Backend submission still recalculates prices and creates price snapshots.

Why:

Square, Toast, Clover, Oracle Simphony, and Revel treat calculated prices, taxes, discounts, and service charges as explicit server-side order/check concepts. IoTables v1 does not need a separate price preview UX because menu prices are stable during ordering, but it still needs server-side price snapshots and a future-safe adjustment model.

Output:

- Define `PriceAdjustment` data model.
- Decide v1 tax behavior: disabled, fixed-rate, or configurable.
- Decide v1 discount/service charge behavior: out of scope or cashier-only.

### 4. Split QR/display ownership before implementation

Decision needed:

- Split current `Table Access / QR` ownership into two internal modules:
  - `Tenant Setup / Table Display Provisioning`
  - `Ordering / Table Presence`
- Keep one end-to-end QR flow document only if it helps explain the full flow.

Why:

Table display credentials are tenant setup/provisioning. Fresh QR presence is ordering security. Keeping both in one module is convenient for docs but weak for encapsulation.

Output:

- Create or split docs before code layout is created.
- Keep `TableDisplayClaim` and `TableDisplayCredential` under Tenant Setup.
- Keep `TableAccessToken` redemption and `presenceValidUntil` under Ordering.

### 5. Lock tenant lifecycle enum

App-level decision:

Minimum v1 enum:

- `provisioning`
- `active`
- `suspended`
- `provisioning_failed`

New tenants start as `provisioning`. They move to `active` after required tenant setup records commit successfully. Manual DNS readiness is tracked as a setup checklist field, not as DNS automation.

Why:

Tenant creation, starter data, DNS/manual readiness, runtime availability, and failure recovery need stable states before migrations.

Output:

- Update PlatformApp docs.
- Update Platform / Tenant Registry module.
- Update `data-model.md`.

### 6. Define mandatory audit events

Decision needed:

Minimum v1 event list:

- `platform_owner.created`
- `platform_owner.totp_enrolled`
- `tenant.created`
- `tenant.provisioning_failed`
- `tenant.activated`
- `tenant.suspended`
- `tenant.gsm_changed`
- `starter_template.applied`
- `user.created`
- `user.disabled`
- `password.changed`
- `otp.verified`
- `table_display.provisioned`
- `table_display.revoked`
- `order.submitted`
- `preparation.status_changed`
- `delivery.status_changed`
- `payment.recorded`
- `session.closed`
- `cashier.correction_applied`

Why:

Audit cannot be a vague utility. Platform, access, money, customer orders, QR/display provisioning, and corrections need consistent event names before critical commands are coded.

Output:

- Update `audit.md`.
- Add audit event names to affected transaction boundaries.

## P1: First End-to-End Flow Blockers

### 7. Define availability and sold-out model

Decision needed:

- Keep `ProductService.available` for catalog-level orderability.
- Add an `AvailabilityOverride` / `SoldOut` model for temporary operational unavailability.
- V1 can avoid stock counts, but must support manual sold-out if menu is live.

Why:

Square, Clover, Toast, SpotOn, Adisyo, Simpra, and DİA distinguish catalog existence from stock/sold-out/availability. A single boolean will become ambiguous quickly.

Output:

- Update Menu Catalog docs.
- Add data model for sold-out override.
- Define who can set sold-out in v1: Tenant Admin only, or station/cashier also.

### 8. Define menu variant and portion pricing

Decision needed:

- Decide whether size/portion is a modifier or a priced variant.
- Recommended direction: use `ProductVariant` for priced size/portion, and keep modifiers for add-ons/options.

Why:

Akınsoft-style usage includes small/half/double portions with distinct prices. Treating all of this as generic modifiers makes pricing, display, and reporting weaker.

Output:

- Update Menu Catalog docs.
- Update CustomerApp product detail/cart docs.
- Update data model with `ProductVariant` if accepted.

### 9. Define kitchen display / printer adapter boundary

Decision needed:

- V1 StationStaffApp is the primary KDS.
- Kitchen printers, receipt printers, ÖKC, cash drawers, and hardware adapters are out of v1 unless explicitly added.
- If added later, they live behind adapter interfaces and domain events, not inside order submission code.

Why:

Odoo, Floreant, Square KDS, Akınsoft, Menulux, GoPOS, and DİA show hardware/KDS as a real restaurant requirement. Even if out of v1, the boundary must be protected.

Output:

- Add adapter boundary note to Fulfillment and Settlement docs.
- Add outbox/domain-event follow-up if hardware printing is deferred.

### 10. Define fiscal / e-Adisyon / ÖKC scope

App-level decision:

- Fiscal/e-Adisyon/ÖKC document creation and receipt issuance are out of v1.
- CashierApp records operational payments only in v1.
- Fiscal Documents remains a future context candidate.

Why:

Akınsoft, DİA, GoPOS, Menulux, and Logo GastroPOS treat e-Adisyon, ÖKC, fiscal receipt links, and legal document flow as core restaurant concerns in Turkey.

Output:

- Add Fiscal context candidate to module map follow-up.
- Do not add `FiscalDocument` / `FiscalDocumentLink` to v1 schema unless legal scope changes.

### 11. Define correction/reversal model

App-level decision:

- V1 allows cashier note-only corrections.
- V1 allows order item cancellation/void only while preparation state is `pending` or `cannot_prepare` and before any payment has been recorded for the TableSession.
- V1 allows payment void only on an open TableSession when no external payment provider is involved.
- V1 does not allow manual items, manual discounts, service fees, refunds after closure, direct price snapshot edits, or cancellation of items already in active preparation/delivery states.
- All corrections require reason, idempotency, authorization, and audit.

Why:

Commercial systems support void, refund, ikram, zayi, item move, split, and discount actions. Without a narrow v1 list, CashierApp becomes an unrestricted history rewrite surface.

Output:

- Update CashierApp docs.
- Update Settlement context docs.
- Update Audit mandatory event list.

### 12. Define event/outbox strategy

Decision needed:

- In-process domain events are enough for v1, or persistent outbox is required for critical async work.
- Recommended direction: persistent outbox for non-transactional side effects after v1 schema exists.

Why:

Toast and Square expose webhooks for order/menu/availability changes. IoTables is a monolith, but QR display, future printers, fiscal integrations, and notifications still need reliable event boundaries.

Output:

- Add domain event/outbox rule to module map.
- Decide which v1 events are persisted.

## P2: Explicit V1 Out-of-Scope Decisions

These should be documented as deliberate v1 exclusions so the architecture does not accidentally optimize for them.

| Capability | V1 Status | Reason |
| --- | --- | --- |
| Multi-branch / multi-location tenant | Out of scope | Impacts tenant, menu, staff, reporting, and billing schemas |
| Waiter-entered order | Out of scope | Requires staff order channel, staff cart, and cashier/station semantics |
| Customer payment / pay-at-table | Out of scope | Requires payment provider, reconciliation, and customer payment UX |
| Package service / courier / pickup / delivery | Out of scope | Requires delivery channel, address, courier, timing, and dispatch models |
| Counter sale / quick sale | Out of scope | Different order/session model from table QR |
| Floor-plan coordinates | Out of scope | V1 uses ordered hall table grid |
| Item/person-based split payment | Out of scope | Requires Check/GuestCheck line assignment |
| Multi-currency payment | Out of scope | Requires currency, exchange rate, and settlement rules |
| Stock counts / recipe / cost accounting | Out of scope | Requires inventory and recipe domains |
| Campaign / happy hour engine | Out of scope | Requires pricing rule engine |
| Multi-language menu | Out of scope unless required by first tenant | Requires localization model |
| Offline-first POS | Out of scope | Requires local storage, sync, conflict resolution, and duplicate ticket controls |

## P3: Later Architecture Candidates

| Candidate | Trigger |
| --- | --- |
| Fiscal Documents context | e-Adisyon, ÖKC, e-Fatura/e-Arşiv integration enters roadmap |
| Inventory context | Stock counts, recipe, costing, or automatic sold-out enters roadmap |
| Promotions context | Campaign, happy hour, coupon, or discount rules become tenant-configurable |
| Multi-location context | Tenant needs branches with shared catalog or separate operations |
| Hardware Integration context | Kitchen printers, receipt printers, cash drawers, or payment terminals are added |
| External Ordering context | Marketplace, online ordering, pickup/delivery, or phone orders are added |

## Recommended Execution Order

1. Close app-level scenario gaps first.
2. Lock v1 operating scope.
3. Implement Check / Adisyon model in schema and module docs.
4. Add pricing contract: server-side snapshots and price adjustments.
5. Split QR/display ownership.
6. Lock tenant lifecycle enum.
7. Define mandatory audit events.
8. Define availability/sold-out model.
9. Define menu variant/portion pricing.
10. Define hardware adapter boundary.
11. Define fiscal scope.
12. Define correction/reversal model.
13. Define event/outbox strategy.
14. Update `data-model.md`.
15. Update affected module docs.
16. Start backend schema and API contracts.
