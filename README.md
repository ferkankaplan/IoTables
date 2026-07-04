# IoTables

IoTables is a modular monolith for cafe and restaurant ordering workflows.

The product semantics live under `docs/apps/`. Implementation must follow the derivation chain documented in `docs/implementation-readiness.md` and `docs/semantic/source-policy.md`.

## Local Commands

Run the full local Docker smoke stack:

```powershell
docker compose up -d --build
docker compose logs -f backend frontend
```

Open:

- Frontend: `http://localhost:5173`
- API health: `http://localhost:8000/api/v1/health/live`
- API docs: `http://localhost:8000/api/docs`

Stop the full stack:

```powershell
docker compose down
```

Bootstrap the local Platform Owner inside the backend container:

```powershell
docker compose exec backend uv run python -m iotables.tools.bootstrap_platform_owner --username platform --password admin
```

Run the app locally outside Docker:

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

Bootstrap the local Platform Owner explicitly:

```powershell
uv run python -m iotables.tools.bootstrap_platform_owner --username platform --password admin
```

Production must use an environment-owned password and `IOTABLES_SECURITY_SECRET_KEY`; this command is not run automatically by app startup.

## Structure

| Path | Purpose |
| --- | --- |
| `src/iotables/` | FastAPI backend package |
| `migrations/` | Alembic migration environment |
| `compose.yaml` | Local PostgreSQL development service |
| `frontend/` | Vite + React + Tailwind SPA |
| `tests/` | Backend executable tests |
| `docs/` | Semantic source documentation |
