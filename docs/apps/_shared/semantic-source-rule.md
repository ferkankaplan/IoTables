# Semantic Source Rule

The app documentation is the semantic source for IoTables the current release.

Module, schema, API, backend, frontend, and test decisions must implement the app behavior documented under `docs/apps/`. They must not invent parallel product semantics at lower layers.

If a module, schema, API, or UI decision conflicts with app behavior, update the relevant app document first and then merge the downstream design into that decision.

Source order:

1. App definition documents define purpose, users, authority, screens, and limits.
2. App end-to-end documents define each app's role in the cross-app flow.
3. Scenario documents define happy paths and branches.
4. Visibility documents define what each app sees from shared state.
5. Acceptance criteria define when current release behavior is complete.
6. UI state documents define required screen states before detailed UI design.
7. Module, data model, and API documents implement these app decisions.
