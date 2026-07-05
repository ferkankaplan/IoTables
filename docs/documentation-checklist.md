# Implementation Checklist

This file lists the current remaining implementation work. Completed work is removed or moved to a short completion note when the task is finished.

This checklist is a human work queue only. It is not a semantic source and is excluded from `docs/semantic/index.jsonl`.

## Status

| Metric | Value |
| --- | --- |
| Main tasks remaining | 8 |
| Current task | Migration and DB integrity audit |
| Next task | Runtime gap closure for documented current release endpoints |

## Work Queue

- [ ] Migration and DB integrity audit.
  - [ ] Compare SQLAlchemy metadata with Alembic heads.
  - [ ] Run clean database upgrade to head.
  - [ ] Verify local `pnpm run db:migrate` and `pnpm run db:current`.
  - [ ] Document any migration rollback policy gaps.

- [ ] Runtime gap closure for documented current release endpoints.
  - [ ] Review documented endpoints against implemented routers.
  - [ ] Implement or explicitly defer Cashier correction note/item-void endpoints.
  - [ ] Implement or explicitly defer cashier operational audit/history endpoints.
  - [ ] Implement or explicitly defer tenant staff management endpoints.
  - [ ] Remove stale frontend copy such as generic “API bağlantısı sıradaki implementasyon adımı” placeholders where the workspace is already implemented.

- [ ] DB-backed transaction and concurrency tests.
  - [ ] Order submit duplicate/idempotent retry.
  - [ ] Payment record duplicate/idempotent retry and overpayment race.
  - [ ] Payment void duplicate/idempotent retry.
  - [ ] Session close with non-zero balance and duplicate close.
  - [ ] Preparation and delivery invalid transition races.
  - [ ] Bulk delivery one invalid item rollback.

- [ ] Frontend structure cleanup.
  - [ ] Split `frontend/src/App.tsx` into app surface modules.
  - [ ] Extract shared API helpers, auth shell, layout primitives, state blocks, badges, and detail rows.
  - [ ] Preserve current routes and app-surface detection while splitting.

- [ ] Operational audit/history surfaces.
  - [ ] Add CashierApp payment/correction/session evidence view.
  - [ ] Add TenantApp operational audit view where documented.
  - [ ] Keep audit messages app-safe and free of implementation terms.

- [ ] Reliable side-effects worker.
  - [ ] Implement outbox claim/retry/complete/fail loop.
  - [ ] Add worker tests for stale claims and retryable failures.
  - [ ] Connect OTP/SMS delivery to the side-effect policy before real provider integration.

- [ ] Production hardening.
  - [ ] Review required environment variables and secret handling.
  - [ ] Add deployment smoke commands.
  - [ ] Add observability hooks without storing secrets.
  - [ ] Verify CORS/session cookie settings for production hostnames.

- [ ] End-to-end restaurant scenario validation.
  - [ ] Platform creates cafe tenant.
  - [ ] Tenant admin verifies seeded halls, tables, stations, menu, users, and QR display provisioning.
  - [ ] Customer scans QR, adds cart items, and submits order.
  - [ ] Station staff prepares items.
  - [ ] Service staff delivers items.
  - [ ] Cashier records partial/full payment, voids a payment when needed, and closes the session.

## Update Rule

When a task is completed, update the status table and remove completed checklist items. Regenerate `docs/semantic/index.jsonl` only when the completed work changed indexed documentation.
