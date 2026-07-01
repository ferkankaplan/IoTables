# IoTables

IoTables is a modular monolith for cafe and restaurant ordering workflows.

The product semantics live under `docs/apps/`. Implementation must follow the derivation chain documented in `docs/implementation-readiness.md` and `docs/semantic/source-policy.md`.

## Local Commands

```powershell
uv sync
pnpm install
pnpm run lint
pnpm run test
pnpm run build
```

Run the backend API:

```powershell
pnpm run dev:api
```

Run the frontend:

```powershell
pnpm run dev:web
```

## Structure

| Path | Purpose |
| --- | --- |
| `src/iotables/` | FastAPI backend package |
| `migrations/` | Alembic migration environment |
| `frontend/` | Vite + React + Tailwind SPA |
| `tests/` | Backend executable tests |
| `docs/` | Semantic source documentation |
