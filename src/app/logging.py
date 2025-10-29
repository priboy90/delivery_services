from __future__ import annotations

import logging
import sys
from logging.config import dictConfig
from typing import Any

try:
    import orjson
except Exception:
    orjson = None  # type: ignore


class OrjsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        for attr in ("method", "path", "status_code", "duration_ms", "client", "session_id"):
            if hasattr(record, attr):
                payload[attr] = getattr(record, attr)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if orjson:
            return orjson.dumps(payload).decode("utf-8")
        import json

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"json": {"()": OrjsonFormatter}},
            "handlers": {"console": {"class": "logging.StreamHandler", "stream": sys.stdout, "formatter": "json"}},
            "loggers": {
                "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
                "app": {"handlers": ["console"], "level": level, "propagate": False},
                "": {"handlers": ["console"], "level": level},
            },
        }
    )
