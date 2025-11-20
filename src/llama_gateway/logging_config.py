"""Logging configuration for the gateway."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .settings import settings


def setup_logging(log_dir: Optional[str] = None) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_dir: Directory for log files. If None, uses settings.LOG_DIR
    """
    log_dir = log_dir or settings.LOG_DIR
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(levelname)-8s | %(message)s"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(simple_formatter)

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "gateway.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # File handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Configure uvicorn loggers
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").propagate = True
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True

    # Log initialization
    logger = logging.getLogger("llama_gateway")
    logger.info("Logging configured successfully")
    logger.debug(f"Log level: {settings.LOG_LEVEL}")
    logger.debug(f"Log directory: {log_path.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"llama_gateway.{name}")
