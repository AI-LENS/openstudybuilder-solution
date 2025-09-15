import logging
import logging.config
import traceback

from fastapi import Request

from common.config import settings
from common.exceptions import MDRApiBaseException


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;5;240m"
    blue = "\x1b[34m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[1m\x1b[38;5;196m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str | None = None, colors: bool = True):
        super().__init__()
        if fmt is None:
            fmt = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"

        self.fmt = fmt
        self.formats = (
            {
                logging.DEBUG: self.grey + fmt + self.reset,
                logging.INFO: self.blue + fmt + self.reset,
                logging.WARNING: self.yellow + fmt + self.reset,
                logging.ERROR: self.red + fmt + self.reset,
                logging.CRITICAL: self.bold_red + fmt + self.reset,
            }
            if colors
            else {}
        )

    def format(self, record):
        return logging.Formatter(self.formats.get(record.levelno, self.fmt)).format(
            record
        )


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"},
        "custom": {
            "()": CustomFormatter,
            "colors": settings.color_logs,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG" if settings.app_debug else "INFO",
            "formatter": "custom",
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": "DEBUG" if settings.app_debug else "INFO",
    },
    "loggers": {
        "neo4j.notifications": {
            "level": "ERROR",  # silence warning messages from Neo4j db
        }
    },
}


def default_logging_config():
    logging.config.dictConfig(LOGGING_CONFIG)


log = logging.getLogger(__name__)


async def log_exception(request: Request, exception: MDRApiBaseException | Exception):
    if isinstance(exception, MDRApiBaseException):
        log.error(
            "Handled %d %s: %s %s -> %s",
            exception.status_code,
            exception.__class__.__name__,
            request.method,
            request.url,
            exception.msg,
        )
    else:
        log.error(
            "Handled %s: %s %s -> %s",
            exception.__class__.__name__,
            request.method,
            request.url,
            str(getattr(exception, "msg", None) or exception),
        )

    # Log the last 15 entries of the exception's traceback
    log.info(
        "\n".join(
            traceback.format_tb(
                exception.__traceback__, limit=settings.traceback_max_entries
            )
        )
    )

    if not request._stream_consumed and settings.app_debug:
        curl_cmd = f"curl -X {request.method} '{request.url}'"
        for header, value in request.headers.items():
            curl_cmd += f" -H '{header}: {value}'"

        if body := await request.body():
            curl_cmd += f" -d '{body.decode('utf-8')}'"

        log.debug("Reproduce with: %s", curl_cmd)
