import pytest
from click.testing import CliRunner
import os
import json
import shutil
from pathlib import Path
from src.fhir_doc_tool.cli import cli
from src.fhir_doc_tool.server import (
    list_resources_handler,
    get_definition_handler,
    get_field_details_handler,
)

TEST_DATA_DIR = Path("tests/test_data")


@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    """AC1: Setup test data by indexing Patient."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Monkeypatch the DATA_DIR in the source modules
    import src.fhir_doc_tool.cli
    import src.fhir_doc_tool.server

    src.fhir_doc_tool.cli.DATA_DIR = TEST_DATA_DIR
    src.fhir_doc_tool.server.DATA_DIR = TEST_DATA_DIR

    runner = CliRunner()
    runner.invoke(cli, ["index", "--resources", "Patient"])
    yield
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)


def test_cli_index():
    """AC1: Verify index command creates local cache."""
    assert (TEST_DATA_DIR / "Patient.profile.json").exists()
    assert (TEST_DATA_DIR / "Patient.summary.json").exists()


def test_cli_list():
    """AC3: Verify list command returns indexed resources."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Patient" in result.output


def test_cli_query():
    """AC2: Verify query command displays human-readable summary."""
    runner = CliRunner()
    result = runner.invoke(cli, ["query", "Patient"])
    assert result.exit_code == 0
    assert "Resource: Patient" in result.output


@pytest.mark.asyncio
async def test_mcp_list_resources():
    """AC3: Verify MCP tool lists all available resources."""
    result = await list_resources_handler({})
    assert "Patient" in result[0].text


@pytest.mark.asyncio
async def test_mcp_get_definition():
    """AC4, Phase 1.5 AC1-AC3: Verify MCP tool returns minified JSON definition."""
    result = await get_definition_handler({"resource_name": "Patient"})
    definition = json.loads(result[0].text)

    # It should now be a list of elements, not a full StructureDefinition object
    assert isinstance(definition, list)

    # Verify the first element is the root Patient object
    assert definition[0]["path"] == "Patient"

    # Verify minification: fields like 'mapping' or 'constraint' should be gone
    for element in definition:
        assert "mapping" not in element
        assert "constraint" not in element

        # Verify extensions are filtered out
        assert not element["path"].endswith(".extension")
        assert not element["path"].endswith(".modifierExtension")


@pytest.mark.asyncio
async def test_mcp_field_lookup():
    """AC5: Verify MCP tool returns specific field details."""
    result = await get_field_details_handler(
        {"resource_name": "Patient", "field_path": "Patient.active"}
    )
    element = json.loads(result[0].text)
    assert element.get("path") == "Patient.active"
