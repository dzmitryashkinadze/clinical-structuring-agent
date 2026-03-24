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

---

# SDD: Pipeline Orchestration & CLI (Phase 4)

## Feature Description
A command-line interface (CLI) to process a single clinical note (`.txt`, `.md` file, or raw string) using the `ClinicalAnalystAgent`. A dedicated `Validator` component will intercept the agent's raw JSON output to enforce strict `fhir.resources` compliance, dropping invalid objects and preparing the foundation for a future LLM self-correction loop.

## Acceptance Criteria (AC)
- **AC1:** A CLI `src/main.py` is implemented using `click`.
- **AC2:** The `process` command accepts either `--text "Note here"` or `--file path/to/note.txt`.
- **AC3:** The `process` command outputs formatted JSON to `stdout` by default, or saves it if `--out path/to/output.json` is provided.
- **AC4:** A `FHIRValidator` class (`src/validator/fhir_validator.py`) receives raw JSON dicts from the agent.
- **AC5:** The `FHIRValidator` logs `pydantic.ValidationError`s and drops invalid resources, returning only fully instantiated FHIR objects.

## Test Description (TDD - Commit 1)
- `test_validator_success`: Verifies a valid dictionary is instantiated correctly.
- `test_validator_failure_dropped`: Verifies an invalid dictionary (missing required FHIR fields) logs an error and is dropped from the result list.
- `test_cli_process_text`: Mocks the agent and verifies the CLI handles `--text` and `--out` arguments correctly.
- `test_cli_process_file`: Mocks the agent and verifies the CLI reads a file correctly.

---

# SDD: Multi-Agent Validation & Self-Correction (Phase 5)

## Feature Description
An advanced multi-agent orchestration loop to maximize extraction accuracy. A primary Extractor Agent (Gemini) generates FHIR resources. A deterministic Python `FHIRValidator` tags each object as `VALID` or `INVALID` with specific schema errors. This entire package (note, extracted objects, error traces) is evaluated by a secondary Validator Agent (Claude 3.5 Sonnet). The Validator Agent decides whether to accept the bundle or generate comprehensive feedback, which is fed back to the Extractor Agent for up to 3 retries.

## Acceptance Criteria (AC)
- **AC1:** `FHIRValidator` is updated to return detailed validation reports (Status + Errors) instead of just dropping invalid resources.
- **AC2:** A new `ValidatorAgent` powered by Claude 3.5 Sonnet evaluates the Extractor's output and the Python validation report.
- **AC3:** The `ValidatorAgent` outputs a `ValidationDecision` (boolean `accepted`, string `feedback`).
- **AC4:** The `ClinicalAnalystAgent` orchestrates a retry loop (max 3 times), appending the Validator's feedback to its prompt history if rejected.
- **AC5:** The loop breaks early if the Validator accepts the bundle, returning only the resources tagged as `VALID` by Pydantic.
- **AC6:** Unit tests mock a rejection loop and verify the message history correctly appends the feedback and retries.

## Test Description (TDD - Commit 1)
- `test_fhir_validator_report`: Verifies the Python validator correctly tags VALID/INVALID status and captures error strings.
- `test_validator_agent_decision`: Mocks the Claude agent to ensure it returns a structured `ValidationDecision`.
- `test_agent_orchestration_loop`: Verifies the Extractor loop retries up to `MAX_RETRIES` when rejected, and exits early when accepted.

---

# SDD: Clinical Resource Expansion (Phase 6)

## Feature Description
Expand the FHIR extraction pipeline from 7 core resources to comprehensive coverage of all 55 Clinical and Base resources defined in FHIR R4. This enables the system to extract structured data from complex clinical notes covering the full spectrum of patient care: conditions, medications, procedures, care plans, diagnostic reports, care teams, medical devices, and organizational entities. The expansion explicitly excludes Foundation (conformance/metadata), Financial (billing/claims), and Specialized (research/regulatory) resources to maintain focus on direct clinical care documentation.

## Scope: 55 Clinical + Base Resources

### Currently Supported (7)
Patient, Observation, Condition, MedicationRequest, Procedure, AllergyIntolerance, Encounter

### Clinical - Summary (4 new)
AdverseEvent, FamilyMemberHistory, ClinicalImpression, DetectedIssue

### Clinical - Diagnostics (7 new)
DiagnosticReport, Media, Specimen, BodyStructure, ImagingStudy, QuestionnaireResponse, MolecularSequence

### Clinical - Medications (8 new)
Immunization, MedicationAdministration, MedicationDispense, MedicationStatement, Medication, MedicationKnowledge, ImmunizationEvaluation, ImmunizationRecommendation

### Clinical - Care Provision (8 new)
CarePlan, CareTeam, Goal, ServiceRequest, NutritionOrder, VisionPrescription, RiskAssessment, RequestGroup

### Clinical - Request & Response (4 new)
Communication, CommunicationRequest, DeviceRequest, DeviceUseStatement

### Base - Individuals (5 new)
Practitioner, PractitionerRole, RelatedPerson, Person, Group

### Base - Entities (9 new)
Organization, OrganizationAffiliation, HealthcareService, Endpoint, Location, Substance, BiologicallyDerivedProduct, Device, DeviceMetric

### Base - Management (3 new)
EpisodeOfCare, Flag, List

**Total: 55 resources (48 new)**

## Acceptance Criteria (AC)

- **AC1:** The `CORE_RESOURCES` list in `src/fhir_doc_tool/cli.py` includes all 55 clinical and base resources, excluding Foundation, Financial, and Specialized resources.
- **AC2:** Running `fhir-doc index` successfully downloads and caches StructureDefinitions for all 55 resources.
- **AC3:** The `RESOURCE_MAP` in `src/validator/fhir_validator.py` includes Python model mappings for all 55 resource types.
- **AC4:** The FHIRValidator correctly instantiates valid resources of all 55 types and rejects invalid ones with appropriate error messages.
- **AC5:** The Clinical Analyst Agent can query the MCP server for schema definitions of any of the 55 resources.
- **AC6:** End-to-end integration test demonstrates extraction of at least 15 different resource types from a comprehensive clinical note covering conditions, medications, procedures, care plans, diagnostics, care team, and organizational context.
- **AC7:** All documentation (SDD, ARCHITECTURE, README) is updated to reflect the expanded 55-resource scope and explicitly document the exclusion of non-clinical resource categories.

## Test Description (TDD - Commit 1)

- `test_all_55_resources_indexed`: Verifies that all 55 clinical + base resources have corresponding `.profile.json` and `.summary.json` files in `data/fhir_docs/` after indexing.
- `test_validator_supports_all_resources`: Parameterized test that verifies `FHIRValidator` can successfully instantiate each of the 55 resource types from valid dictionaries.
- `test_validator_rejects_invalid_resources`: Verifies that invalid data for each resource category is properly rejected with error messages.
- `test_comprehensive_clinical_note_extraction`: Integration test using a synthetic clinical note (`data/notes/comprehensive.txt`) that contains clinical content triggering extraction of 15+ different resource types including Patient, Practitioner, Organization, Encounter, Condition, MedicationRequest, Observation, DiagnosticReport, Procedure, CarePlan, CareTeam, Goal, AllergyIntolerance, FamilyMemberHistory, and Immunization.
- `test_mcp_serves_all_55_resources`: Verifies the MCP server can successfully serve schema definitions for all 55 resources via the `get_resource_definition` tool.
