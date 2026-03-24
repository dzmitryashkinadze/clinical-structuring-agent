from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    GOOGLE_API_KEY: str  # Use GOOGLE_API_KEY to satisfy pydantic-ai's GoogleProvider
    ANTHROPIC_API_KEY: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    MCP_SERVER_COMMAND: str = "uv"
    MCP_SERVER_ARGS: str = "run,python,src/fhir_doc_tool/server.py"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
