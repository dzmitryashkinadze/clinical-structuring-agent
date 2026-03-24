# Application Architecture: Agentic EHR-to-FHIR Pipeline

## Overview
The system is a modular pipeline that transforms unstructured clinical notes into validated HL7 FHIR R4 resources. It separates the **Source of Truth (Documentation)** from the **Processing Logic (Agents)**.

## Core Components

### 1. FHIR Doc Tool (`src/fhir_doc_tool/`)
- **Purpose:** (Current Phase) Local knowledge base for FHIR R4.
- **Interfaces:**
    - **CLI:** For manual indexing (`index`), listing (`list`), and querying (`query`).
    - **MCP Server:** For LLM agents to fetch schema definitions in real-time.
- **Storage:** Local cache in `data/fhir_docs/`.

### 2. Clinical Analyst Agent (`src/clinical_analyst/`)
- **Purpose:** Extraction agent powered by **Pydantic AI** and **Gemini 3 Flash**.
- **Logic:**
    - `config.py`: Centralized settings (API keys, MCP paths) using `pydantic-settings`.
    - `mcp_client.py`: Bridge to the FHIR Doc Tool MCP server.
    - `agent.py`: LLM reasoning loop that consults the Doc Tool and maps text to `fhir.resources`.
- **Flow:** Lookup (MCP) -> Plan -> Extract -> Validate.
- **Output:** List of `fhir.resources` Python objects.

### 3. Standardizer (`src/standardizer/`)
- **Purpose:** Terminology mapping and semantic standardization.
- **Logic:**
    - `nci_client.py`: Python client for the National Cancer Institute (NCI) Enterprise Vocabulary Services (EVS) REST API.
    - Resolves raw clinical terms to standard ontologies (e.g., SNOMED-CT, LOINC) without requiring an API key.
- **Output:** Structured `Coding` arrays for `CodeableConcept` fields.

### 4. Validator & CLI (`src/validator/`, `src/main.py`)
- **Purpose:** Final schema enforcement, multi-agent evaluation, and CLI orchestration.
- **Logic:**
    - `main.py`: `click`-based CLI to process single notes (`--text` or `--file`) and output valid FHIR JSON to `stdout` or `--out`.
    - `fhir_validator.py`: Python module that strictly evaluates LLM outputs against `fhir.resources`, generating a detailed report (VALID/INVALID + error strings) for each object.
    - `agent.py`: A secondary **Validator Agent** powered by **Anthropic Claude 3.5 Sonnet**. It consumes the Extractor's context and the Python validation report. It outputs a `ValidationDecision` (Accept/Reject) and detailed feedback.
- **Feedback Loop:** If rejected, the Extractor Agent receives the Validator's feedback and retries (up to 3 times).
- **Output:** A strict array of validated `fhir.resources` models.

## Data Flow
`Raw Note` -> `Clinical Analyst (w/ Doc Tool)` -> `Standardizer` -> `Validator` -> `Output JSON`

## File Structure
- `src/`: Component logic.
- `tests/`: TDD suites (mirrors `src/` structure).
- `scripts/`: Verification and maintenance scripts.
- `data/fhir_docs/`: Local FHIR spec cache (JSON/HTML).
