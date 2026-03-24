import asyncio
import logging
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from .config import settings
from .mcp_client import FHIRDocClient

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Define a union of common resources for extraction
FHIRResource = Union[Patient, Observation, Condition]


class ExtractionResult(BaseModel):
    """Result of the FHIR extraction."""

    resources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A list of FHIR resources identified in the text.",
    )


from pydantic_ai.providers.google import GoogleProvider


class ClinicalAnalystAgent:
    """AC5: Agent that identifies, lookups, and extracts FHIR resources from clinical notes."""

    def __init__(self, mcp_client: Optional[FHIRDocClient] = None):
        self.mcp_client = mcp_client or FHIRDocClient()
        self.model = GoogleModel(
            "gemini-3-flash-preview",
            provider=GoogleProvider(api_key=settings.GOOGLE_API_KEY),
        )

        self.agent = Agent(
            self.model,
            output_type=ExtractionResult,
            system_prompt=(
                "You are a Clinical Analyst Agent. Your goal is to transform unstructured clinical notes into HL7 FHIR R4 JSON resources. "
                "Follow the 'Lookup-then-Extract' flow:\n"
                "1. Use 'list_available_resources' to see what FHIR types are available.\n"
                "2. Use 'get_fhir_schema' for the types you identify in the note.\n"
                "3. Use 'get_field_details' if you need clarification on specific paths.\n"
                "4. Map the note content to valid FHIR JSON.\n"
                "If no clinical data is found, return an empty list of resources."
            ),
        )

        # Register tools
        @self.agent.tool_plain
        async def list_available_resources() -> List[str]:
            """AC3: List all locally indexed FHIR resources."""
            return await self.mcp_client.list_resources()

        @self.agent.tool_plain
        async def get_fhir_schema(resource_name: str) -> Dict[str, Any]:
            """AC4: Get the full StructureDefinition for a FHIR resource."""
            return await self.mcp_client.get_resource_definition(resource_name)

        @self.agent.tool_plain
        async def get_field_details(
            resource_name: str, field_path: str
        ) -> Dict[str, Any]:
            """AC5: Get descriptions and constraints for a specific field path."""
            return await self.mcp_client.get_field_details(resource_name, field_path)

    async def run(self, note: str) -> List[Any]:
        """AC2, AC4: Run the agent on a clinical note and return validated FHIR objects."""
        try:
            result = await self.agent.run(note)
            extracted_data = result.output.resources

            validated_resources = []
            for item in extracted_data:
                res_type = item.get("resourceType")
                try:
                    # Dynamically instantiate the fhir.resources class
                    if res_type == "Patient":
                        validated_resources.append(Patient(**item))
                    elif res_type == "Observation":
                        validated_resources.append(Observation(**item))
                    elif res_type == "Condition":
                        validated_resources.append(Condition(**item))
                    else:
                        logger.warning(
                            f"Resource type {res_type} not currently supported for direct validation."
                        )
                except Exception as e:
                    logger.error(f"Validation error for {res_type}: {e}")

            return validated_resources

        except Exception as e:
            import traceback

            logger.error(f"Agent execution failed: {e}")
            logger.error(traceback.format_exc())
            return []
