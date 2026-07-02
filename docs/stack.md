# Technology Stack

This document records the intended IoTables stack and the currently verified local tooling.

## Runtime Targets

| Area | Technology | Version |
| --- | --- | --- |
| Backend language | Python | 3.14.6 |
| Frontend runtime | Node.js | 24.18.0 |
| Database | PostgreSQL | 18.4 |
| Frontend package manager | pnpm | 11.0.0 |
| Python package manager | uv | 0.11.25 |

## Backend Stack

| Purpose | Technology | Target Version |
| --- | --- | --- |
| API framework | FastAPI | latest compatible with Python 3.14 |
| ORM | SQLAlchemy | 2.x async |
| Database migrations | Alembic | latest compatible |
| PostgreSQL driver | asyncpg | latest compatible |
| Settings/config | Pydantic Settings | 2.x |
| TOTP secret encryption | cryptography | latest compatible |
| Testing | pytest | latest compatible |
| Async test support | pytest-asyncio | latest compatible |
| HTTP test client | httpx2 | latest compatible |
| Lint/format | Ruff | latest compatible |
| Migration timestamp timezone data | tzdata | latest compatible |

## Frontend Stack

| Purpose | Technology | Target Version |
| --- | --- | --- |
| UI library | React | 19.2.0 |
| Language | TypeScript | 6.0.3 |
| Build tool | Vite | latest compatible |
| Styling | Tailwind CSS | 4.x |
| Tailwind integration | `@tailwindcss/vite` | 4.x |

## Infrastructure and Tooling

| Purpose | Technology | Verified Version |
| --- | --- | --- |
| Version control | Git | 2.54.0.windows.1 |
| GitHub CLI | gh | 2.95.0 |
| Local PostgreSQL service | Docker Compose `db` service | `postgres:18.4`, exposed on `localhost:5433` |
| PostgreSQL CLI | `psql` | 18.4 |
| PostgreSQL bin path | `C:\Program Files\PostgreSQL\18\bin` | Added to user PATH; reopen terminals to inherit |
| Container runtime | Docker | 29.5.3 |
| Container orchestration | Docker Compose | 5.1.4 |

## Repository Standards

| File | Purpose |
| --- | --- |
| `AGENTS.md` | Agent behavior and architectural working rules |
| `.gitignore` | Ignored local, generated, cache, secret, and build files |
| `.gitattributes` | Line ending and binary file handling |
| `.editorconfig` | Cross-editor formatting defaults |
| `compose.yaml` | Local PostgreSQL 18.4 development service |

## Architectural Direction

- Frontend: Vite + React single-page application.
- Backend: FastAPI API service.
- Database: PostgreSQL with Alembic migrations; local development uses the Docker Compose `db` service instead of the host PostgreSQL service.
- Tenant model: platform-owned tenants, each representing a cafe or restaurant customer.
- Package layout: monorepo structure, with app boundaries added as the project grows.
