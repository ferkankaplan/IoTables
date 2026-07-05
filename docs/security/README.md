# Security Documentation

This directory defines current release security requirements that cut across apps, modules, API standards, database transactions, and operations.

Security documents do not replace module ownership. They summarize threats, required controls, and verification expectations across the existing semantic sources.

## Documents

| Document | Purpose |
| --- | --- |
| [threat-model.md](threat-model.md) | V1 threat model for QR abuse, fake orders, OTP abuse, tenant isolation, session theft, duplicate submit, and cashier/payment misuse. |
| [rate-limits.md](rate-limits.md) | V1 rate limit strategy for public, customer, staff, OTP, QR, payment, and internal worker surfaces. |

## Source Boundaries

- App documents define user-visible behavior and user-facing failure states.
- Module documents define command guards, invariants, and ownership.
- API documents define auth, CSRF, idempotency, error envelopes, and response safety.
- Database documents define hard constraints, locking, transaction, and rollback behavior.
- Security documents define cross-layer abuse cases and ensure the above layers remain synchronized.

If a security document conflicts with an app, module, API, or database source, repair the owning source first and then update this directory.
