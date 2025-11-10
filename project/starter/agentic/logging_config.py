import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        # Custom extras
        for key in ("ticket_id", "user_id", "agent", "route", "tool", "status"):
            if hasattr(record, key):
                log[key] = getattr(record, key)
        return json.dumps(log, ensure_ascii=False)


def configure_logging(log_path: str = "logs/agentic.log") -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers in interactive runs
    if any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        return
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


