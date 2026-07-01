# Semantic Source Policy

This document defines how IoTables documentation must be read as semantic source material.

It is not a user work queue and not an implementation schedule. Its purpose is to keep app intent, module boundaries, data models, API contracts, tests, and code synchronized.

## Semantic Foundation

The six apps are the product foundation:

- PlatformApp
- TenantApp
- CustomerApp
- StationStaffApp
- ServiceStaffApp
- CashierApp

Every module, bounded context, database model, API contract, workflow, test, and implementation detail exists to serve these apps and their documented scenarios.

If a lower layer cannot be traced back to an app scenario, it is either missing its semantic source or it is out of scope.

## Derivation Chain

Use this order when creating, reviewing, indexing, or implementing behavior:

1. App scenario
2. App workflow and branch behavior
3. App UI state, permission, and visibility rules
4. Module responsibility and ownership boundary
5. Module command, event, invariant, and integration contract
6. Data model, transaction, rollback, and retention rule
7. API request, response, authorization, idempotency, and error contract
8. Test scenario and acceptance criteria
9. Implementation code and runtime configuration
10. Generated or derived artifacts such as semantic index records

This order is semantic, not chronological. A later discovery may force a correction in an earlier layer.

## Conflict Resolution

When two layers conflict, resolve the highest owning semantic layer first.

- App-level product behavior outranks module shape.
- Module ownership outranks data-table convenience.
- Domain invariants outrank API convenience.
- Data integrity outranks frontend assumptions.
- Source Markdown outranks generated index records.

Do not patch the downstream layer while leaving the upstream contradiction in place. Repair the source decision, then propagate the correction forward through affected modules, data models, APIs, tests, code, and generated artifacts.

## Indexing Rule

The semantic index should include source documents that define behavior, ownership, contracts, invariants, or traceability.

ADRs under `docs/adr/` are semantic source documents for locked cross-cutting architecture decisions. They explain why a decision is fixed; they do not replace the app, module, data, API, or test documents that define the operational detail.

The semantic index must not treat human planning files as source truth. A checklist can mention future work, but it does not define product behavior unless the same decision is merged into the owning app, module, data, API, or test document.

When indexing or retrieving context, prefer this path:

1. Exact source path, app, module, endpoint, command, or semantic ID match.
2. ADR records when the question is about a locked architecture decision.
3. App scenario and workflow records.
4. Module contract records.
5. Data and API contract records.
6. Test and acceptance records.
7. Broader semantic similarity only after exact ownership has been checked.

## Implementation Rule

Before writing code for a behavior:

- identify the app scenario that creates the need;
- identify the owning module and its contract;
- identify the data and transaction rules that keep the behavior safe;
- identify the API contract exposed to the app;
- identify the tests that prove the behavior and its branch cases;
- only then write the implementation.

If one of these references is missing, create or repair the owning documentation before coding unless the user explicitly narrows the task to exploration.

## Traceability Rule

Code and tests may reference `semantic_id` values from `docs/semantic/index.jsonl`, but those references are pointers only.

The semantic decision must remain in the owning Markdown source. Code comments, test names, and generated index records must not become hidden product specifications.
