"""
Logging configuration for Trend & Viral Engine Pro.
Provides structured JSON logging with context.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from src.core.config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """Setup application logging with loguru."""
    # Remove default logger
    logger.remove()

    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File logging (JSON format)
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    logger.add(
        log_path / "trend-engine-{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="00:00",
        retention="30 days",
        compression="gz",
        serialize=True,  # JSON format
        backtrace=True,
        diagnose=True,
    )

    # Error-only file
    logger.add(
        log_path / "errors-{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="gz",
        serialize=True,
        backtrace=True,
        diagnose=True,
    )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept uvicorn/fastapi logging
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info(f"Logging configured (level={settings.log_level}, env={settings.environment})")


def get_logger(name: str) -> Any:
    """Get a logger instance with the given name."""
    return logger.bind(service=name)


# Setup logging on import
setup_logging()
