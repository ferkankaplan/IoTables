# IoTables

IoTables is a modular monolith for cafe and restaurant ordering workflows.

The product semantics live under `docs/apps/`. Implementation must follow the derivation chain documented in `docs/implementation-readiness.md` and `docs/semantic/source-policy.md`.

## Local Commands

```powershell
uv sync
pnpm install
pnpm run db:up
pnpm run db:migrate
pnpm run lint
pnpm run test
pnpm run build
```

Run the local PostgreSQL 18.4 service:

```powershell
pnpm run db:up
pnpm run db:migrate
pnpm run db:current
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
| `compose.yaml` | Local PostgreSQL development service |
| `frontend/` | Vite + React + Tailwind SPA |
| `tests/` | Backend executable tests |
| `docs/` | Semantic source documentation |
