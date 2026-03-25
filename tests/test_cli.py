import pytest
import os
import tempfile
from click.testing import CliRunner
from unittest.mock import AsyncMock

from src.main import cli
from fhir.resources.patient import Patient


@pytest.fixture
def mock_agent_run(mocker):
    """Mocks the agent.run to return empty raw dicts."""
    # We mock the ClinicalAnalystAgent so it doesn't hit Gemini
    # It now returns instantiated objects since we changed the agent in Phase 2
    mock = mocker.patch("src.main.ClinicalAnalystAgent.run", new_callable=AsyncMock)
    # The agent returns fully validated resources now
    mock.return_value = [Patient(id="test-1")]
    return mock


def test_cli_process_text(mock_agent_run):
    """AC1, AC2: Verify CLI processes text directly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["process", "--text", "Sample note here"])

    assert result.exit_code == 0
    assert "Patient" in result.output
    assert "test-1" in result.output


def test_cli_process_file(mock_agent_run):
    """AC1, AC2: Verify CLI reads a file."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Sample note in file")
        f_path = f.name

    try:
        result = runner.invoke(cli, ["process", "--file", f_path])
        assert result.exit_code == 0
        assert mock_agent_run.called
    finally:
        os.remove(f_path)


def test_cli_process_out_file(mock_agent_run):
    """AC3: Verify CLI saves output to a JSON file."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as out_f:
        out_path = out_f.name

    try:
        result = runner.invoke(cli, ["process", "--text", "Note", "--out", out_path])
        assert result.exit_code == 0

        with open(out_path, "r") as f:
            content = f.read()
            assert "test-1" in content
    finally:
        os.remove(out_path)
