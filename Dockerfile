FROM ghcr.io/astral-sh/uv:python3.14-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "iotables.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
