import logging
import json
from typing import List, Dict, Any, Union
from pydantic import ValidationError, BaseModel
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from fhir.resources.encounter import Encounter
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.procedure import Procedure
from fhir.resources.allergyintolerance import AllergyIntolerance

logger = logging.getLogger(__name__)


class FHIRValidator:
    """AC4: Wrapper component to validate raw dicts against strict fhir.resources schemas."""

    # Mapping of resourceType strings to their corresponding fhir.resources Pydantic models
    RESOURCE_MAP = {
        "Patient": Patient,
        "Observation": Observation,
        "Condition": Condition,
        "Encounter": Encounter,
        "MedicationRequest": MedicationRequest,
        "Procedure": Procedure,
        "AllergyIntolerance": AllergyIntolerance,
    }

    def validate_bundle(self, resources: List[Dict[str, Any]]) -> List[BaseModel]:
        """AC5: Iterates through raw LLM outputs, drops invalid ones, returns instantiated models."""
        valid_resources = []

        for item in resources:
            res_type = item.get("resourceType")

            if not res_type:
                logger.error("Validation error: Item missing 'resourceType'")
                continue

            model_class = self.RESOURCE_MAP.get(res_type)
            if not model_class:
                logger.warning(
                    f"Validation warning: Resource type '{res_type}' is not currently supported by the Validator."
                )
                continue

            try:
                # Attempt to instantiate the Pydantic model
                valid_instance = model_class(**item)
                valid_resources.append(valid_instance)
            except ValidationError as e:
                # Log the specific missing/invalid fields for potential future self-correction
                logger.error(f"Validation error for {res_type} (dropped): {e}")
            except Exception as e:
                logger.error(
                    f"Unexpected error instantiating {res_type} (dropped): {e}"
                )

        return valid_resources
