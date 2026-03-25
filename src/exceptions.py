"""
Custom exception classes for domain-specific errors.

This module defines exceptions used throughout the FHIR structuring pipeline
to provide clear, actionable error messages for different failure scenarios.
"""

__all__ = [
    "FHIRAgentError",
    "FHIRValidationError",
    "TerminologyServiceError",
    "MCPConnectionError",
    "PromptLoadError",
    "ConfigurationError",
]


class FHIRAgentError(Exception):
    """Base exception for all FHIR agent errors."""

    pass


class FHIRValidationError(FHIRAgentError):
    """
    Raised when FHIR resource validation fails.

    This typically indicates schema compliance issues or missing required fields.
    """

    pass


class TerminologyServiceError(FHIRAgentError):
    """
    Raised when terminology service API calls fail.

    This can occur due to network errors, API errors, or invalid terminology systems.
    """

    pass


class MCPConnectionError(FHIRAgentError):
    """
    Raised when MCP server connection fails.

    This typically indicates the MCP server is not running or unreachable.
    """

    pass


class PromptLoadError(FHIRAgentError):
    """
    Raised when prompt files cannot be loaded.

    This typically indicates missing or unreadable prompt files.
    """

    pass


class ConfigurationError(FHIRAgentError):
    """
    Raised when configuration is invalid or missing.

    This typically indicates missing required API keys or invalid settings.
    """

    pass
