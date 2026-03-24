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
- **Purpose:** (Future) Terminology mapping using the NLM API.

### 4. Validator (`src/validator/`)
- **Purpose:** (Future) Schema enforcement and feedback loops.

## Data Flow
`Raw Note` -> `Clinical Analyst (w/ Doc Tool)` -> `Standardizer` -> `Validator` -> `Output JSON`

## File Structure
- `src/`: Component logic.
- `tests/`: TDD suites (mirrors `src/` structure).
- `scripts/`: Verification and maintenance scripts.
- `data/fhir_docs/`: Local FHIR spec cache (JSON/HTML).
