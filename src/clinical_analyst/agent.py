import asyncio
import logging
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from fhir.resources.encounter import Encounter
from .config import settings
from .mcp_client import FHIRDocClient
from src.standardizer.nci_client import NCIClient, TerminologyMatch
import json

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


class ExtractionResult(BaseModel):
    """Result of the FHIR extraction. MUST be valid JSON string."""

    fhir_json_bundle: str = Field(
        description="A JSON string representing an array of FHIR resources."
    )


from pydantic_ai.providers.google import GoogleProvider


class ClinicalAnalystAgent:
    """AC5: Agent that identifies, lookups, and extracts FHIR resources from clinical notes."""

    def __init__(
        self,
        mcp_client: Optional[FHIRDocClient] = None,
        nci_client: Optional[NCIClient] = None,
    ):
        self.mcp_client = mcp_client or FHIRDocClient()
        self.nci_client = nci_client or NCIClient()
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
                "3. Use 'search_terminology' to look up standardized FHIR codes for medical concepts (e.g. SNOMED-CT for conditions, LOINC for observations).\n"
                "4. Map the note content to valid FHIR JSON.\n\n"
                "IMPORTANT INSTRUCTIONS:\n"
                "- Output ONLY a JSON array of fully-populated FHIR resources.\n"
                "- You must use full nested JSON objects/arrays (e.g., Patient.name is an array of objects).\n"
                "- Do NOT invent random integers to replace complex objects.\n"
                "- If a concept can be coded, use 'search_terminology' and put the result in a `CodeableConcept.coding` array.\n"
                "- If no data is found, output '[]'.\n"
                "- The result should be provided as a RAW JSON string in the `fhir_json_bundle` field."
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

        @self.agent.tool_plain
        async def search_terminology(
            query: str, terminology: str = "snomedct_us"
        ) -> Optional[Dict[str, str]]:
            """Phase 3 AC3: Search for official FHIR codes (SNOMED-CT, LOINC, etc.) for a medical concept.
            Use 'snomedct_us' for conditions/diseases/procedures.
            Use 'loinc' for observations/measurements.
            Returns a Coding object {system, code, display} or None if not found.
            """
            logger.info(f"Looking up term: '{query}' in {terminology}")
            match = await self.nci_client.search_concept(query, terminology)
            if match:
                return match.model_dump()
            return None

    async def run(self, note: str) -> List[Any]:
        """AC2, AC4: Run the agent on a clinical note and return validated FHIR objects."""
        try:
            result = await self.agent.run(note, message_history=[])

            # Print conversation history before trying to parse the output
            logger.info("\n========== LLM MESSAGES AND MCP CALLS ==========")
            for msg in result.all_messages():
                logger.info("-" * 40)
                if hasattr(msg, "parts"):
                    for part in msg.parts:
                        logger.info(f"[{type(part).__name__}]")
                        if hasattr(part, "content"):
                            logger.info(part.content)
                        if hasattr(part, "tool_name"):
                            logger.info(f"Tool Call: {part.tool_name}")
                            if hasattr(part, "args"):
                                logger.info(f"Args: {part.args}")
                        if hasattr(part, "tool_name") and hasattr(
                            part, "content"
                        ):  # ToolReturn
                            logger.info(
                                f"Return from {part.tool_name}: {str(part.content)[:200]}..."
                            )
                else:
                    logger.info(str(msg))
            logger.info("===============================================\n")

            try:
                extracted_data = json.loads(result.output.fhir_json_bundle)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode LLM output as JSON: {e}")
                return []

            if not isinstance(extracted_data, list):
                logger.error(
                    f"LLM returned a {type(extracted_data)} instead of a list."
                )
                return []

            logger.info("Raw extracted resources from LLM:")
            for item in extracted_data:
                logger.info(json.dumps(item, indent=2))

            validated_resources = []
            for item in extracted_data:
                res_type = item.get("resourceType")
                try:
                    if res_type == "Patient":
                        validated_resources.append(Patient(**item))
                    elif res_type == "Observation":
                        validated_resources.append(Observation(**item))
                    elif res_type == "Condition":
                        validated_resources.append(Condition(**item))
                    elif res_type == "Encounter":
                        validated_resources.append(Encounter(**item))
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
