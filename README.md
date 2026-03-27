# Clinical Structuring Agent

[![CI](https://github.com/dzmitryashkinadze/clinical-structuring-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/dzmitryashkinadze/clinical-structuring-agent/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dzmitryashkinadze/clinical-structuring-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/dzmitryashkinadze/clinical-structuring-agent)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

An agentic AI pipeline that transforms unstructured clinical notes into structured, validated healthcare data formats. **FHIR-first implementation** with planned support for OMOP CDM, openEHR, and HL7 v2.

## Vision

Transform clinical free text into any standardized healthcare format using multi-agent AI:
- **HL7 FHIR R4** (current implementation - 52 resource types)
- **OMOP CDM** (roadmap - Q2 2026)
- **openEHR** (roadmap - Q3 2026)
- **HL7 v2 Messages** (roadmap - Q4 2026)

## Current Features (FHIR R4)

- **Comprehensive Resource Coverage:** Supports all 52 clinical and base FHIR R4 resources (conditions, medications, procedures, diagnostics, care plans, care teams, organizations, and more)
- **Multi-Agent Architecture:** Primary extraction agent (Claude Sonnet 4.6) + Validator agent (GPT-5.4) with self-correction loop
- **Clinical Analyst Agent:** Parses clinical notes and maps them to FHIR resources using dynamic schema lookup via MCP
- **Terminology Mapping:** Free NCI EVS API integration for SNOMED-CT/LOINC standardization (no API key required)
- **Iterative Validation:** Multi-agent feedback loop with up to 3 retries for accuracy
- **FHIR Doc Tool:** Local MCP server with minified schemas (96% size reduction) for fast, offline schema compliance

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
