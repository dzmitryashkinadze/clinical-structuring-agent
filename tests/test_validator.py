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
