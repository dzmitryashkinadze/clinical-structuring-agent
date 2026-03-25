from src.validator.fhir_validator import FHIRValidator


def test_validator_report_success():
    """AC1: Verify a valid dictionary gets a VALID status."""
    validator = FHIRValidator()
    valid_data = [{"resourceType": "Patient", "id": "123", "gender": "male"}]

    reports = validator.evaluate_bundle(valid_data)

    assert len(reports) == 1
    assert reports[0].status == "VALID"
    assert not reports[0].errors
    assert reports[0].resource.id == "123"


def test_validator_report_failure():
    """AC1: Verify an invalid dictionary gets an INVALID status and error strings."""
    validator = FHIRValidator()
    invalid_data = [{"resourceType": "Patient", "gender": 123}]  # Invalid gender type

    reports = validator.evaluate_bundle(invalid_data)

    assert len(reports) == 1
    assert reports[0].status == "INVALID"
    assert reports[0].resource is None
    assert len(reports[0].errors) > 0
    assert "gender" in reports[0].errors[0]


def test_validator_report_unsupported():
    """AC1: Verify an unsupported resource type gets an INVALID status."""
    validator = FHIRValidator()
    unsupported_data = [{"resourceType": "MadeUpResource", "id": "123"}]

    reports = validator.evaluate_bundle(unsupported_data)

    assert len(reports) == 1
    assert reports[0].status == "INVALID"
    assert "not currently supported" in reports[0].errors[0]
