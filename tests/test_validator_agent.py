import pytest
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from src.validator.agent import ValidatorAgent, ValidationDecision
from src.validator.fhir_validator import ValidationReport
from fhir.resources.patient import Patient


@pytest.mark.asyncio
async def test_validator_agent_decision(mocker):
    """AC2, AC3: Verify Claude agent evaluates the context and outputs a ValidationDecision."""
    mock_run = mocker.patch("pydantic_ai.Agent.run", new_callable=AsyncMock)
    mock_run.return_value.output = ValidationDecision(
        accepted=False, feedback="The patient resource is missing a valid telecom list."
    )

    agent = ValidatorAgent()
    reports = [
        ValidationReport(
            raw_dict={"resourceType": "Patient", "telecom": 123},
            status="INVALID",
            errors=["telecom must be a list"],
        )
    ]

    decision = await agent.evaluate_bundle(
        note="Patient Doe. Phone 555-1234",
        extractor_messages=[],
        validation_reports=reports,
    )

    assert isinstance(decision, ValidationDecision)
    assert decision.accepted is False
    assert "missing a valid telecom list" in decision.feedback
