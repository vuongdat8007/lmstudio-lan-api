# src/lmstudio_gateway/logging_config.py
"""
Logging configuration for LM Studio LAN Gateway.
Sets up structured logging with appropriate formatters and handlers.
"""
import logging
import logging.config

from .settings import settings


def configure_logging() -> None:
    """
    Configure application logging based on settings.

    Sets up:
    - Standard formatter for application logs
    - Access formatter for HTTP access logs
    - Console handler for all logs
    - Log levels from settings
    """
    log_level = settings.LOG_LEVEL

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: "
                '%(client_addr)s - "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            # Root logger
            "": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            # Uvicorn loggers
            "uvicorn": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
            # Application logger
            "lmstudio_gateway": {
                "handlers": ["default"],
                "level": log_level,
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
