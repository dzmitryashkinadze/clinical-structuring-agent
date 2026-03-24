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

# SDD: MCP Schema Minification (Phase 1.5)

## Feature Description
The raw FHIR `StructureDefinition` JSON files are too large (~193KB for Patient) and contain unnecessary XML mappings, constraints, and base definitions, overwhelming the LLM context window. The MCP server must intercept and minify the schema before returning it to the agent.

## Acceptance Criteria (AC)
- **AC1:** The `get_resource_definition` MCP tool returns a minified list of elements instead of the full `StructureDefinition`.
- **AC2:** The minified output retains only essential fields: `path`, `min`, `max`, `type`, `short`, and `binding`.
- **AC3:** The minifier filters out elements with paths ending in `.extension`, `.modifierExtension`, or `.id` (except the root resource `id`).
- **AC4:** The output size is reduced significantly.

## Test Description (TDD - Commit 1)
- `test_mcp_get_definition`: Updated to verify that the returned JSON is a list of elements, not a full `StructureDefinition` object, and that it lacks fields like `mapping`.

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

---

# SDD: Terminology Standardizer (Phase 3)

## Feature Description
The Standardizer allows the agent to map unstructured clinical terminology (e.g., "Hypertension") to official FHIR interoperability codes (e.g., SNOMED-CT, LOINC). Instead of generating raw strings in `CodeableConcept.text`, the agent can now construct fully qualified `Coding` entries. It queries the free, open NCI Enterprise Vocabulary Services (EVS) REST API.

## Acceptance Criteria (AC)
- **AC1:** An `NCIClient` component queries the NCI EVS search endpoint `https://api-evsrest.nci.nih.gov/api/v1/concept/[terminology]/search`.
- **AC2:** The client can return the first match containing the `code`, `name` (display), and `terminology` (system).
- **AC3:** The agent registers a `search_terminology` tool to access this client.
- **AC4:** The `NCIClient` handles HTTP errors or no-match scenarios gracefully (returning `None`).
- **AC5:** Unit tests verify the HTTP logic using `httpx` request mocking or `pytest-httpx`.

## Test Description (TDD - Commit 1)
- `test_nci_client_success`: Mocks a successful 200 OK response from the NCI API and verifies parsing of `code` and `name`.
- `test_nci_client_not_found`: Mocks a 404 or empty response and ensures the client returns `None`.
- `test_nci_client_http_error`: Mocks a 500 error to verify the client handles it without crashing.
