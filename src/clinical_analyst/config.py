"""
Configuration management for the FHIR structuring agent.

This module provides centralized configuration using Pydantic Settings,
loading values from environment variables and .env file.

Environment variables can be set in .env file or system environment.
See .env.example for all available options.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    Required settings will raise validation errors if not provided.

    Attributes:
        GOOGLE_API_KEY: API key for Google Gemini (required)
        ANTHROPIC_API_KEY: API key for Anthropic Claude (optional)
        GEMINI_MODEL_NAME: Gemini model identifier
        CLAUDE_MODEL_NAME: Claude model identifier
        MAX_VALIDATION_RETRIES: Maximum retry attempts for validation loop
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
        LOG_FORMAT: Python logging format string
        MCP_SERVER_COMMAND: Command to start MCP server
        MCP_SERVER_ARGS: Arguments for MCP server command
        NCI_API_BASE_URL: Base URL for NCI terminology API
        FHIR_SPEC_BASE_URL: Base URL for HL7 FHIR specification
        FHIR_DOCS_DIR: Directory for cached FHIR documentation
        PROMPTS_DIR: Directory containing agent prompt files
        DEFAULT_TERMINOLOGY: Default terminology system for code lookups
    """

    # API Keys
    OPENAI_API_KEY: Optional[str] = None  # Primary extraction model
    GOOGLE_API_KEY: Optional[str] = None  # Alternative extraction model
    ANTHROPIC_API_KEY: Optional[str] = None  # Validation model

    # Model Configuration
    OPENAI_MODEL_NAME: str = Field(default="gpt-4o")
    OPENAI_VALIDATOR_MODEL_NAME: str = Field(default="gpt-5.4")  # For validation agent
    GEMINI_MODEL_NAME: str = Field(default="gemini-3-flash-preview")
    CLAUDE_MODEL_NAME: str = Field(default="claude-sonnet-4-6")

    # Model Selection (which provider to use for extraction and validation)
    EXTRACTION_MODEL_PROVIDER: str = Field(
        default="anthropic"
    )  # "openai", "google", or "anthropic"
    VALIDATION_MODEL_PROVIDER: str = Field(default="openai")  # "openai" or "anthropic"

    # Pipeline Configuration
    MAX_VALIDATION_RETRIES: int = Field(default=3, ge=1, le=10)

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # MCP Configuration
    MCP_SERVER_COMMAND: str = Field(default="uv")
    MCP_SERVER_ARGS: str = Field(default="run,python,src/fhir_doc_tool/server.py")

    # API Endpoints
    NCI_API_BASE_URL: str = Field(default="https://api-evsrest.nci.nih.gov/api/v1")
    FHIR_SPEC_BASE_URL: str = Field(default="https://hl7.org/fhir/R4/")

    # File Paths
    FHIR_DOCS_DIR: Path = Field(default=Path("data/fhir_docs"))
    PROMPTS_DIR: Path = Field(default=Path("prompts"))

    # Terminology Configuration
    DEFAULT_TERMINOLOGY: str = Field(default="snomedct_us")

    # HTTP Configuration
    HTTP_RETRY_ATTEMPTS: int = Field(default=3, ge=1, le=10)
    HTTP_RETRY_MIN_WAIT: int = Field(default=2, ge=1)
    HTTP_RETRY_MAX_WAIT: int = Field(default=10, ge=1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Global settings instance
settings = Settings()
