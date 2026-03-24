# Agentic AI EHR-to-FHIR Extraction

An agentic pipeline that transforms unstructured clinical notes into valid, interoperable FHIR R4 Python objects and JSON. **Supports 52 clinical and base resource types** covering the full spectrum of patient care documentation.

## Features

- **Comprehensive Resource Coverage:** Supports all 52 clinical and base FHIR R4 resources (3 excluded: Media, RequestGroup, DeviceUseStatement - not available in fhir.resources) (conditions, medications, procedures, diagnostics, care plans, care teams, organizations, and more)
- **Multi-Agent Architecture:** Primary extraction agent (Gemini 3 Flash) + Validator agent (Claude Sonnet 4.6) with self-correction loop
- **Clinical Analyst Agent:** Parses clinical notes and maps them to FHIR resources using dynamic schema lookup
- **Terminology Mapping:** Free NCI EVS API integration for SNOMED-CT/LOINC standardization (no API key required)
- **Iterative Validation:** Multi-agent feedback loop with up to 3 retries for accuracy
- **FHIR Doc Tool:** Local MCP server with minified schemas for fast, offline schema compliance

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

## Supported FHIR Resources (52 Total)

### Clinical Resources

**Summary (7):** Patient, Condition, Procedure, AllergyIntolerance, AdverseEvent, FamilyMemberHistory, ClinicalImpression, DetectedIssue

**Diagnostics (8):** Observation, DiagnosticReport, Media, Specimen, BodyStructure, ImagingStudy, QuestionnaireResponse, MolecularSequence

**Medications (9):** MedicationRequest, Immunization, MedicationAdministration, MedicationDispense, MedicationStatement, Medication, MedicationKnowledge, ImmunizationEvaluation, ImmunizationRecommendation

**Care Provision (8):** Encounter, CarePlan, CareTeam, Goal, ServiceRequest, NutritionOrder, VisionPrescription, RiskAssessment, RequestGroup

**Request & Response (4):** Communication, CommunicationRequest, DeviceRequest, DeviceUseStatement

### Base Resources

**Individuals (6):** Patient, Practitioner, PractitionerRole, RelatedPerson, Person, Group

**Entities (10):** Organization, OrganizationAffiliation, HealthcareService, Endpoint, Location, Substance, BiologicallyDerivedProduct, Device, DeviceMetric

**Management (4):** Encounter, EpisodeOfCare, Flag, List

**Note:** Foundation (conformance/metadata), Financial (billing/claims), and Specialized (research/regulatory) resources are explicitly excluded.

## Pipeline Architecture

For more details on the agentic design, see [AGENTS.md](./AGENTS.md) and [ARCHITECTURE.md](./ARCHITECTURE.md).
