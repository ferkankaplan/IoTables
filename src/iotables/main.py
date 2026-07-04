from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from iotables import __version__
from iotables.api.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from iotables.api.router import api_router
from iotables.config import Settings, get_settings
from iotables.database.session import create_database_engine, create_database_sessionmaker
from iotables.middleware import request_context_middleware
from iotables.observability import configure_logging
from iotables.security.session import DatabaseSessionResolver


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    database_engine = create_database_engine(resolved_settings)
    database_session_factory = create_database_sessionmaker(database_engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await app.state.database_engine.dispose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.database_engine = database_engine
    app.state.database_session_factory = database_session_factory
    app.state.session_resolver = DatabaseSessionResolver(database_session_factory)
    app.middleware("http")(request_context_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "X-CSRF-Token",
            "X-Request-Id",
            "X-Tenant-Subdomain",
        ],
    )

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
