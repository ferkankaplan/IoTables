# Branch Coverage Checklist
Before API contracts are finalized, each v1 endpoint or command should map to at least one scenario above and explicitly declare:

- happy path;
- invalid input branch;
- unauthorized branch;
- stale state branch;
- duplicate/idempotent retry branch where applicable;
- concurrent mutation branch where applicable;
- transaction failure behavior where applicable;
- visible app outcome.
