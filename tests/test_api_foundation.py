import json
import logging

from fastapi import HTTPException
from fastapi.testclient import TestClient

from iotables.api.errors import ApiError
from iotables.main import create_app
from iotables.observability import JsonLogFormatter


def test_request_id_header_is_echoed_when_safe() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/health/live",
        headers={"X-Request-Id": "client_req-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "client_req-123"


def test_invalid_request_id_header_is_replaced() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/health/live",
        headers={"X-Request-Id": "bad request id with spaces"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"].startswith("req_")
    assert response.headers["X-Request-Id"] != "bad request id with spaces"


def test_validation_errors_use_standard_error_envelope() -> None:
    app = create_app()

    @app.get("/api/test/validation")
    async def validation_probe(limit: int) -> dict[str, int]:
        return {"limit": limit}

    client = TestClient(app)

    response = client.get(
        "/api/test/validation?limit=not-an-int",
        headers={"X-Request-Id": "req_validation"},
    )

    assert response.status_code == 422
    assert response.headers["X-Request-Id"] == "req_validation"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["error"] == {
        "code": "validation_failed",
        "message": "Some fields are invalid.",
        "requestId": "req_validation",
        "details": {},
        "fieldErrors": [
            {
                "path": "limit",
                "code": "int_parsing",
                "message": "Input should be a valid integer, unable to parse string as an integer",
            }
        ],
    }


def test_http_exception_uses_standard_error_envelope() -> None:
    app = create_app()

    @app.get("/api/test/not-found")
    async def not_found_probe() -> None:
        raise HTTPException(status_code=404)

    client = TestClient(app)

    response = client.get(
        "/api/test/not-found",
        headers={"X-Request-Id": "req_not_found"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found_or_hidden",
            "message": "Resource was not found.",
            "requestId": "req_not_found",
            "details": {},
            "fieldErrors": [],
        }
    }


def test_domain_api_error_uses_standard_error_envelope() -> None:
    app = create_app()

    @app.get("/api/test/domain-error")
    async def domain_error_probe() -> None:
        raise ApiError(
            status_code=409,
            code="invalid_state",
            message="The current state does not allow this action.",
        )

    client = TestClient(app)

    response = client.get(
        "/api/test/domain-error",
        headers={"X-Request-Id": "req_domain"},
    )

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "invalid_state",
        "message": "The current state does not allow this action.",
        "requestId": "req_domain",
        "details": {},
        "fieldErrors": [],
    }


def test_unhandled_exception_returns_safe_internal_error() -> None:
    app = create_app()

    @app.get("/api/test/unhandled")
    async def unhandled_probe() -> None:
        raise RuntimeError("raw secret diagnostic")

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get(
        "/api/test/unhandled",
        headers={"X-Request-Id": "req_internal"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "An unexpected error occurred.",
            "requestId": "req_internal",
            "details": {},
            "fieldErrors": [],
        }
    }
    assert "raw secret diagnostic" not in response.text


def test_json_log_formatter_does_not_treat_python_module_as_domain_module() -> None:
    record = logging.LogRecord(
        name="iotables.http",
        level=logging.INFO,
        pathname="src/iotables/middleware.py",
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )
    record.requestId = "req_log"

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["requestId"] == "req_log"
    assert "module" not in payload

    record.moduleContext = "Ordering"

    payload_with_module = json.loads(JsonLogFormatter().format(record))

    assert payload_with_module["module"] == "Ordering"
