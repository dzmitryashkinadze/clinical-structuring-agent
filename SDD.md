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
