"""
Centralized logging configuration for the FHIR structuring agent.

This module provides a single point of configuration for application-wide logging,
ensuring consistent log formats and levels across all modules.
"""

import logging
import sys
from typing import Optional, Protocol


class SettingsProtocol(Protocol):
    """Protocol for settings objects."""

    LOG_LEVEL: str
    LOG_FORMAT: str


# Import settings at module level to avoid circular imports
# This will be called before other modules import their loggers
try:
    from ..clinical_analyst.config import settings as _imported_settings

    _settings: SettingsProtocol = _imported_settings
except ImportError:
    # Fallback for testing or standalone scripts
    class FallbackSettings:
        LOG_LEVEL = "INFO"
        LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    _settings = FallbackSettings()


def setup_logging(
    log_level: Optional[str] = None, log_format: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.

    This should be called once at application startup, typically from main.py.
    Calling it multiple times will reconfigure logging with the new settings.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  If None, uses settings.LOG_LEVEL
        log_format: Python logging format string.
                   If None, uses settings.LOG_FORMAT

    Example:
        >>> setup_logging()  # Use settings from config
        >>> setup_logging(log_level="DEBUG")  # Override to DEBUG
    """
    level = log_level or _settings.LOG_LEVEL
    format_str = log_format or _settings.LOG_FORMAT

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Reconfigure if already configured
    )

    # Silence noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("h11").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={level}, format={format_str[:50]}...")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    This is a convenience function that ensures consistent logger naming.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)
