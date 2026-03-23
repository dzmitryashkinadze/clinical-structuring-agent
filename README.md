# Agentic AI EHR-to-FHIR Extraction

An agentic pipeline that transforms unstructured clinical notes into valid, interoperable FHIR Python objects and JSON.

## Features

- **Clinical Analyst Agent:** Parses clinical notes and maps them to FHIR resources.
- **Terminology Mapping:** Algorithmic querying of the NLM Terminology Service for SNOMED-CT/LOINC.
- **Back-and-Forth Validation:** Iterative refinement of FHIR objects until they pass schema validation.
- **FHIR Doc Tool:** Integrated access to HL7 FHIR documentation to ensure schema compliance.

## Getting Started

1.  **Environment Setup:**
    ```bash
    uv venv
    source .venv/bin/activate
    uv sync
    ```

2.  **Configuration:**
    - Copy `.env.example` to `.env`.
    - Provide your **NLM Terminology Service (UMLS)** API key.

## Pipeline Architecture

For more details on the agentic design, see [AGENTS.md](./AGENTS.md).
