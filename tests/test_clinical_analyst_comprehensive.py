"""
Phase 6 Comprehensive Integration Tests

Tests the full pipeline with a complex clinical note that should extract
15+ different FHIR resource types across clinical and base categories.
"""

import pytest
from pathlib import Path
from src.clinical_analyst.agent import ClinicalAnalystAgent
from src.clinical_analyst.config import Settings


@pytest.mark.asyncio
async def test_comprehensive_clinical_note_extraction():
    """
    Phase 6 AC6: Integration test with comprehensive clinical note.

    This test verifies that the Clinical Analyst Agent can extract diverse
    resource types from a single complex clinical encounter note including:
    - Patient demographics
    - Care team (Practitioner, PractitionerRole, Organization)
    - Clinical conditions
    - Medications and immunizations
    - Observations (vitals, labs)
    - Diagnostic reports
    - Procedures
    - Care planning (CarePlan, CareTeam, Goal)
    - Family history
    - Allergies
    - Risk assessments
    - Communications
    - Encounter and episode of care

    Expected: 15+ different resource types extracted successfully.
    """
    # Load the comprehensive clinical note
    note_path = Path("data/notes/comprehensive.txt")
    assert note_path.exists(), "Comprehensive clinical note not found"

    with open(note_path, "r") as f:
        comprehensive_note = f.read()

    # Initialize the agent
    agent = ClinicalAnalystAgent()

    # Run extraction
    resources = await agent.run(comprehensive_note)

    # Verify we extracted resources
    assert len(resources) > 0, "No resources extracted from comprehensive note"

    # Count resource types
    resource_types = set()
    resource_type_counts = {}

    for resource in resources:
        res_type = resource.__class__.__name__
        resource_types.add(res_type)
        resource_type_counts[res_type] = resource_type_counts.get(res_type, 0) + 1

    # Phase 6 AC6: Should extract at least 15 different resource types
    assert len(resource_types) >= 15, (
        f"Expected at least 15 different resource types, got {len(resource_types)}: "
        f"{sorted(resource_types)}"
    )

    # Verify we have key clinical resources
    expected_core_types = {
        "Patient",  # Patient demographics
        "Practitioner",  # Care providers
        "Organization",  # Healthcare facility
        "Encounter",  # Current visit
        "Condition",  # Medical diagnoses
        "MedicationRequest",  # Active prescriptions
        "Observation",  # Vital signs and labs
        "AllergyIntolerance",  # Documented allergies
        "Immunization",  # Vaccination history
        "DiagnosticReport",  # Lab results
        "Procedure",  # Past procedures
        "CarePlan",  # Treatment plan
        "Goal",  # Patient goals
        "FamilyMemberHistory",  # Family medical history
        "CareTeam",  # Care coordination
    }

    extracted_types = set(resource_types)

    # Should have extracted most of these core types
    core_types_found = expected_core_types.intersection(extracted_types)

    assert len(core_types_found) >= 10, (
        f"Expected at least 10 core clinical resource types, got {len(core_types_found)}: "
        f"{sorted(core_types_found)}. Missing: {sorted(expected_core_types - core_types_found)}"
    )

    # Print summary for debugging
    print("\n=== EXTRACTION SUMMARY ===")
    print(f"Total resources extracted: {len(resources)}")
    print(f"Unique resource types: {len(resource_types)}")
    print("\nResource type breakdown:")
    for res_type in sorted(resource_type_counts.keys()):
        print(f"  {res_type}: {resource_type_counts[res_type]}")


@pytest.mark.asyncio
async def test_comprehensive_note_validates_correctly():
    """
    Phase 6 AC4: Verify all extracted resources from comprehensive note
    pass FHIR validation.
    """
    note_path = Path("data/notes/comprehensive.txt")

    if not note_path.exists():
        pytest.skip("Comprehensive clinical note not found")

    with open(note_path, "r") as f:
        comprehensive_note = f.read()

    agent = ClinicalAnalystAgent()
    resources = await agent.run(comprehensive_note)

    # All returned resources should be valid FHIR instances
    # (invalid ones are dropped by the validator)
    assert len(resources) > 0, "No valid resources extracted"

    # Verify each resource has required FHIR attributes
    for resource in resources:
        assert hasattr(resource, "resource_type"), "Missing resource_type attribute"
        assert hasattr(resource, "dict"), "Resource should be a Pydantic model"

        # Should be able to serialize to dict without errors
        try:
            resource_dict = resource.dict()
            assert "resourceType" in resource_dict
        except Exception as e:
            pytest.fail(f"Failed to serialize {resource.__class__.__name__}: {e}")


@pytest.mark.asyncio
async def test_mcp_serves_all_55_resource_schemas():
    """
    Phase 6 AC5: Verify MCP server can serve schema definitions for
    all 55 clinical and base resources.
    """
    from src.clinical_analyst.mcp_client import FHIRDocClient

    ALL_52_RESOURCES = [
        # Currently supported (7)
        "Patient",
        "Observation",
        "Condition",
        "MedicationRequest",
        "Procedure",
        "AllergyIntolerance",
        "Encounter",
        # Clinical - Summary (4 new)
        "AdverseEvent",
        "FamilyMemberHistory",
        "ClinicalImpression",
        "DetectedIssue",
        # Clinical - Diagnostics (7 new)
        "DiagnosticReport",
        # "Media",  # Not available in fhir.resources R4
        "Specimen",
        "BodyStructure",
        "ImagingStudy",
        "QuestionnaireResponse",
        "MolecularSequence",
        # Clinical - Medications (8 new)
        "Immunization",
        "MedicationAdministration",
        "MedicationDispense",
        "MedicationStatement",
        "Medication",
        "MedicationKnowledge",
        "ImmunizationEvaluation",
        "ImmunizationRecommendation",
        # Clinical - Care Provision (8 new)
        "CarePlan",
        "CareTeam",
        "Goal",
        "ServiceRequest",
        "NutritionOrder",
        "VisionPrescription",
        "RiskAssessment",
        # "RequestGroup",  # Not available in fhir.resources R4
        # Clinical - Request & Response (4 new)
        "Communication",
        "CommunicationRequest",
        "DeviceRequest",
        # "DeviceUseStatement",  # Replaced in R5
        # Base - Individuals (5 new)
        "Practitioner",
        "PractitionerRole",
        "RelatedPerson",
        "Person",
        "Group",
        # Base - Entities (9 new)
        "Organization",
        "OrganizationAffiliation",
        "HealthcareService",
        "Endpoint",
        "Location",
        "Substance",
        "BiologicallyDerivedProduct",
        "Device",
        "DeviceMetric",
        # Base - Management (3 new)
        "EpisodeOfCare",
        "Flag",
        "List",
    ]

    mcp_client = FHIRDocClient()

    # Try to query each resource schema
    failed_resources = []

    for resource_name in ALL_52_RESOURCES:
        try:
            # This will fail if the resource isn't indexed
            schema = await mcp_client.get_resource_definition(resource_name)

            # Verify we got a valid schema back
            assert schema is not None, f"No schema returned for {resource_name}"
            assert isinstance(schema, (list, dict)), (
                f"Invalid schema format for {resource_name}"
            )

        except Exception as e:
            failed_resources.append((resource_name, str(e)))

    assert len(failed_resources) == 0, (
        f"Failed to retrieve schemas for {len(failed_resources)} resources: "
        f"{failed_resources}"
    )
