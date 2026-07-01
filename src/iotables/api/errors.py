from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

REQUEST_ID_STATE_KEY = "request_id"


@dataclass(frozen=True)
class FieldError:
    path: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class ApiError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: dict[str, Any] = field(default_factory=dict)
    field_errors: list[FieldError] = field(default_factory=list)


DEFAULT_ERROR_MESSAGES: dict[int, tuple[str, str]] = {
    400: ("bad_request", "Bad request."),
    401: ("unauthenticated", "Authentication is required."),
    403: ("not_authorized", "You are not allowed to perform this action."),
    404: ("not_found_or_hidden", "Resource was not found."),
    409: ("invalid_state", "The current state does not allow this action."),
    410: ("gone", "This resource is no longer available."),
    422: ("validation_failed", "Some fields are invalid."),
    429: ("rate_limit_exceeded", "Too many requests."),
    500: ("internal_error", "An unexpected error occurred."),
    503: ("tenant_unavailable", "The service is temporarily unavailable."),
}


def get_request_id(request: Request) -> str:
    value = getattr(request.state, REQUEST_ID_STATE_KEY, None)
    if isinstance(value, str) and value:
        return value
    return "req_unavailable"


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    field_errors: list[FieldError] | None = None,
) -> JSONResponse:
    request_id = get_request_id(request)
    request.state.error_code = code

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
                "details": details or {},
                "fieldErrors": [error.as_dict() for error in field_errors or []],
            }
        },
        headers={
            "X-Request-Id": request_id,
            "Cache-Control": "no-store",
        },
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(
        request,
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        field_errors=exc.field_errors,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    http_phrase = HTTPStatus(exc.status_code).phrase if exc.status_code in HTTPStatus else "Error."
    default_code, default_message = DEFAULT_ERROR_MESSAGES.get(
        exc.status_code,
        ("http_error", http_phrase),
    )

    code = default_code
    message = default_message
    details: dict[str, Any] = {}
    field_errors: list[FieldError] = []

    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code", default_code))
        message = str(exc.detail.get("message", default_message))
        raw_details = exc.detail.get("details", {})
        if isinstance(raw_details, dict):
            details = raw_details
    elif exc.detail and str(exc.detail) != http_phrase:
        message = str(exc.detail)

    return error_response(
        request,
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
        field_errors=field_errors,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    field_errors = [
        FieldError(
            path=format_error_path(error.get("loc", ())),
            code=str(error.get("type", "validation_error")).replace(".", "_"),
            message=str(error.get("msg", "Invalid value.")),
        )
        for error in exc.errors()
    ]

    return error_response(
        request,
        status_code=422,
        code="validation_failed",
        message="Some fields are invalid.",
        field_errors=field_errors,
    )


def format_error_path(location: Any) -> str:
    if not isinstance(location, (list, tuple)):
        return "request"

    parts: list[str] = []
    for item in location:
        if item in {"body", "query", "path", "header", "cookie"}:
            continue
        if isinstance(item, int) and parts:
            parts[-1] = f"{parts[-1]}[{item}]"
        elif isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(str(item))

    return ".".join(parts) if parts else "request"
