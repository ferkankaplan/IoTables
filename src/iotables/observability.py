import json
import logging
from typing import Any

SAFE_RECORD_FIELDS = (
    ("requestId", "requestId"),
    ("correlationId", "correlationId"),
    ("tenantId", "tenantId"),
    ("appScope", "appScope"),
    ("actorType", "actorType"),
    ("module", "moduleContext"),
    ("route", "route"),
    ("method", "method"),
    ("statusCode", "statusCode"),
    ("errorCode", "errorCode"),
    ("durationMs", "durationMs"),
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for output_field, record_field in SAFE_RECORD_FIELDS:
            value = getattr(record, record_field, None)
            if value is not None:
                payload[output_field] = value
        if record.exc_info:
            payload["exceptionClass"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(log_level: str) -> None:
    logger = logging.getLogger("iotables")
    logger.setLevel(log_level)
    logger.propagate = False

    handler = _get_iotables_handler(logger)
    handler.setLevel(log_level)
    handler.setFormatter(JsonLogFormatter())


def _get_iotables_handler(logger: logging.Logger) -> logging.Handler:
    for handler in logger.handlers:
        if getattr(handler, "_iotables_handler", False):
            return handler

    handler = logging.StreamHandler()
    handler._iotables_handler = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return handler
