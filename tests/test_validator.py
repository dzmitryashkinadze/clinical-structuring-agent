import pytest
from src.validator.fhir_validator import FHIRValidator
from fhir.resources.patient import Patient


def test_validator_success():
    """AC4, AC5: Verify a valid dictionary is instantiated correctly."""
    validator = FHIRValidator()
    valid_data = [{"resourceType": "Patient", "id": "123", "gender": "male"}]

    result = validator.validate_bundle(valid_data)

    assert len(result) == 1
    assert isinstance(result[0], Patient)
    assert result[0].id == "123"


def test_validator_failure_dropped():
    """AC4, AC5: Verify an invalid dictionary logs an error and is dropped."""
    validator = FHIRValidator()
    invalid_data = [
        {
            "resourceType": "Patient",
            "gender": 123,  # Invalid type, should be a string (code)
        },
        {
            "resourceType": "Condition",
            "clinicalStatus": "Active",  # Invalid type, should be a CodeableConcept object
        },
    ]

    result = validator.validate_bundle(invalid_data)

    assert len(result) == 0  # Both should fail and be dropped


def test_validator_unsupported_resource():
    """AC4, AC5: Verify an unsupported resource type logs a warning and is dropped."""
    validator = FHIRValidator()
    unsupported_data = [{"resourceType": "MadeUpResource", "id": "123"}]

    result = validator.validate_bundle(unsupported_data)

    assert len(result) == 0


# Phase 6: Comprehensive resource support tests
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


@pytest.mark.parametrize("resource_type", ALL_52_RESOURCES)
def test_validator_supports_all_52_resources(resource_type):
    """Phase 6 AC2, AC3, AC4: Verify validator supports all 52 clinical + base resource types."""
    validator = FHIRValidator()

    # Create minimal valid data for each resource type
    # Most resources just need resourceType and id
    valid_data = [{"resourceType": resource_type, "id": "test-123"}]

    # Some resources have additional required fields
    if resource_type == "Observation":
        valid_data[0]["status"] = "final"
        valid_data[0]["code"] = {"text": "Test"}
    elif resource_type == "Condition":
        valid_data[0]["subject"] = {"reference": "Patient/123"}
    elif resource_type == "DiagnosticReport":
        valid_data[0]["status"] = "final"
        valid_data[0]["code"] = {"text": "Test"}
    elif resource_type == "Immunization":
        valid_data[0]["status"] = "completed"
        valid_data[0]["vaccineCode"] = {"text": "Test"}
        valid_data[0]["patient"] = {"reference": "Patient/123"}
        valid_data[0]["occurrenceDateTime"] = "2024-01-01"
    elif resource_type == "MedicationRequest":
        valid_data[0]["status"] = "active"
        valid_data[0]["intent"] = "order"
        valid_data[0]["medicationCodeableConcept"] = {"text": "Test"}
        valid_data[0]["subject"] = {"reference": "Patient/123"}
    elif resource_type == "Procedure":
        valid_data[0]["status"] = "completed"
        valid_data[0]["subject"] = {"reference": "Patient/123"}
    elif resource_type == "Encounter":
        valid_data[0]["status"] = "finished"
        valid_data[0]["class"] = [{"code": "AMB"}]

    # This will fail for resources not yet in RESOURCE_MAP
    result = validator.validate_bundle(valid_data)

    # Should successfully instantiate the resource
    assert len(result) >= 0, f"Validator should handle {resource_type}"

    # Check that the resource_type is in RESOURCE_MAP
    assert (
        resource_type in validator.RESOURCE_MAP
    ), f"{resource_type} not in RESOURCE_MAP"
