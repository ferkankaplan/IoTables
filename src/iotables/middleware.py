import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from fastapi import Request, Response

from iotables.api.errors import error_response
from iotables.security.context import ActorContext

REQUEST_ID_HEADER = "X-Request-Id"
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

logger = logging.getLogger("iotables.http")


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id

    started_at = time.perf_counter()
    status_code = 500
    response: Response

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        request.state.error_code = "internal_error"
        logger.exception(
            "Unhandled API exception",
            extra={
                "requestId": request_id,
                "route": safe_route(request),
            },
        )
        response = error_response(
            request,
            status_code=500,
            code="internal_error",
            message="An unexpected error occurred.",
        )
        status_code = response.status_code

    response.headers[REQUEST_ID_HEADER] = request_id
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")

    duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
    safe_context = request_log_context(request)
    logger.info(
        "HTTP request completed",
        extra={
            "requestId": request_id,
            "route": safe_route(request),
            "method": request.method,
            "statusCode": status_code,
            "errorCode": getattr(request.state, "error_code", None),
            "durationMs": duration_ms,
            **safe_context,
        },
    )
    return response


def resolve_request_id(header_value: str | None) -> str:
    if header_value and REQUEST_ID_RE.fullmatch(header_value):
        return header_value
    return f"req_{uuid4().hex}"


def safe_route(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return request.url.path


def request_log_context(request: Request) -> dict[str, Any]:
    actor = getattr(request.state, "actor", None)
    if not isinstance(actor, ActorContext):
        return {}

    context: dict[str, Any] = {
        "actorType": actor.actor_type.value,
        "appScope": actor.app_scope.value,
    }
    if actor.tenant_id is not None:
        context["tenantId"] = str(actor.tenant_id)
    return context
