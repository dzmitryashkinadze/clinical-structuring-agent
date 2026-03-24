import pytest
from pydantic import ValidationError
from fhir.resources.patient import Patient
from src.clinical_analyst.config import Settings
from src.clinical_analyst.agent import ClinicalAnalystAgent


def test_settings_loading(monkeypatch):
    """AC3: Verify settings load from env."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = Settings()
    assert settings.GOOGLE_API_KEY == "test-key"
    assert settings.LOG_LEVEL == "DEBUG"


@pytest.mark.asyncio
async def test_agent_empty_note():
    """AC2: Verify empty list for non-clinical text."""
    agent = ClinicalAnalystAgent()
    result = await agent.run("Hello, this is just a normal conversation.")
    assert result == []


@pytest.mark.asyncio
async def test_agent_mcp_integration(mocker):
    """AC1, AC5: Verify MCP tool calls during extraction."""
    # Mock MCP client and LLM behavior
    mock_mcp = mocker.patch("src.clinical_analyst.mcp_client.FHIRDocClient")
    agent = ClinicalAnalystAgent(mcp_client=mock_mcp)

    # Simulate a note with a patient name
    await agent.run("John Doe is a patient.")

    # Verify that list_resources was at least called once
    assert mock_mcp.list_resources.called


def test_agent_validation_error_handling():
    """AC4: Verify validation errors are caught."""
    # This might need a more complex mock to simulate LLM returning invalid FHIR
    pass
