# SDD: FHIR Doc Tool (Phase 1)

## Feature Description
A local utility to query the HL7 FHIR R4 specification. It eliminates runtime internet dependencies for the extraction agent and ensures schema compliance.

## Acceptance Criteria (AC)
- **AC1:** `fhir-doc index` downloads and stores R4 `StructureDefinition` (JSON) and summaries for core clinical resources.
- **AC2:** `fhir-doc query <Resource>` displays a human-readable summary from the local cache.
- **AC3:** `fhir-doc list` (CLI & MCP) returns all locally indexed resources.
- **AC4:** MCP Tool `get_resource_definition` returns the full JSON definition of a resource.
- **AC5:** MCP Tool `get_field_details` returns descriptions/constraints for a specific path (e.g., `Observation.status`).
- **AC6:** Minimal code footprint (Priority: Less code, higher reliability).

## Test Description (TDD - Commit 1)
- `test_cli_index`: Verifies files are created in `data/fhir_docs/`.
- `test_cli_list`: Verifies output of indexed resources.
- `test_mcp_definition`: Verifies valid JSON is returned via MCP.
- `test_mcp_field_lookup`: Verifies metadata extraction for specific fields.

---

# SDD: Clinical Analyst Integration (Phase 2)

## Feature Description
An extraction agent powered by Pydantic AI and Gemini 3 Flash. It uses the FHIR Doc Tool (Phase 1) to retrieve schema definitions and constraints, mapping raw clinical text into validated FHIR R4 objects.

## Acceptance Criteria (AC)
- **AC1:** Agent connects to the FHIR Doc Tool MCP server via `stdio` and dynamically selects tools (e.g., `get_resource_definition`).
- **AC2:** Agent returns a `list` of `fhir.resources` objects. Returns an empty list `[]` if no clinical data is identified.
- **AC3:** All configurations (API keys, MCP paths, log levels) are managed via `.env` using a Pydantic `BaseSettings` model.
- **AC4:** The agent handles exceptions (LLM timeouts, MCP connection failures, ValidationErrors) gracefully with logging.
- **AC5:** Implements a "Lookup-then-Extract" flow: identifies resource types first, then fetches schema, then extracts.
- **AC6:** Minimal code footprint using Pydantic AI's native tool calling and dependency injection.

## Test Description (TDD - Commit 1)
- `test_settings_loading`: Verifies that configuration is correctly loaded from the environment.
- `test_agent_empty_note`: Verifies the agent returns an empty list for non-clinical text.
- `test_agent_mcp_integration`: Mocks the MCP server to verify that the agent calls the correct tools when clinical entities are present.
- `test_agent_validation_error`: Verifies that if `fhir.resources` validation fails, it's caught and handled.
