# IoTables

IoTables is a multi-tenant ordering and table session platform for cafes and restaurants.

## Stack

- Backend: Python 3.14, FastAPI, SQLAlchemy 2 async, Alembic, asyncpg
- Frontend: React 19.2, TypeScript 6.0.3, Vite, Tailwind CSS 4
- Database: PostgreSQL 18.4
- Workspace: pnpm

## Project Structure

- `apps/api`: FastAPI backend
- `apps/web`: React frontend
- `migrations`: Alembic database migrations

## Backend

Install dependencies:

```sh
uv sync
```

Run API:

```sh
uv run uvicorn iotables.main:app --app-dir apps/api --reload
```

Run tests:

```sh
uv run pytest
```

Run lint:

```sh
uv run ruff check .
```

## Frontend

Install dependencies:

```sh
pnpm install
```

Run web app:

```sh
pnpm dev:web
```

Build web app:

```sh
pnpm build:web
```

## Environment

Copy `.env.example` to `.env` and adjust values for local development.
