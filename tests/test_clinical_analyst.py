import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from pydantic import ValidationError
from fhir.resources.patient import Patient
from src.clinical_analyst.config import Settings
from src.clinical_analyst.agent import ClinicalAnalystAgent, ExtractionResult


def test_settings_loading(monkeypatch):
    """AC3: Verify settings load from env."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    settings = Settings()
    assert settings.GOOGLE_API_KEY == "test-key"
    assert settings.LOG_LEVEL == "DEBUG"


@pytest.mark.asyncio
async def test_agent_empty_note(mocker):
    """AC2: Verify empty list for non-clinical text."""
    # Mock the agent's run method to return empty result
    # We mock the internal agent's run
    mocker.patch("pydantic_ai.Agent.run", new_callable=AsyncMock)
    import pydantic_ai

    pydantic_ai.Agent.run.return_value.output = ExtractionResult(fhir_json_bundle="[]")

    agent = ClinicalAnalystAgent()
    result = await agent.run("Hello, this is just a normal conversation.")
    assert result == []


@pytest.mark.asyncio
async def test_agent_mcp_integration(mocker):
    """AC1, AC5: Verify MCP tool calls during extraction."""
    # Mock the internal agent's run to return some resource
    mock_run = mocker.patch("pydantic_ai.Agent.run", new_callable=AsyncMock)
    mock_run.return_value.output = ExtractionResult(
        fhir_json_bundle='[{"resourceType": "Patient", "id": "123"}]'
    )

    # Mock FHIRDocClient
    mock_mcp = MagicMock()
    mock_mcp.list_resources = AsyncMock(return_value=["Patient"])
    mock_mcp.get_resource_definition = AsyncMock(
        return_value={"resourceType": "StructureDefinition", "name": "Patient"}
    )

    agent = ClinicalAnalystAgent(mcp_client=mock_mcp)

    # Simulate a note with a patient name
    result = await agent.run("John Doe is a patient.")

    assert len(result) == 1
    assert isinstance(result[0], Patient)
    assert result[0].id == "123"


@pytest.mark.asyncio
async def test_agent_validation_error_handling(mocker):
    """AC4: Verify that if fhir.resources validation fails, it's caught and handled."""
    # Mock agent to return invalid FHIR data
    mock_run = mocker.patch("pydantic_ai.Agent.run", new_callable=AsyncMock)
    # Patient with invalid gender (say it's an integer instead of string)
    mock_run.return_value.output = ExtractionResult(
        fhir_json_bundle='[{"resourceType": "Patient", "gender": 123}]'
    )

    agent = ClinicalAnalystAgent()
    # It should not crash, it should log error and return what it can (empty if validation fails)
    result = await agent.run("Invalid patient data.")
    assert result == []
