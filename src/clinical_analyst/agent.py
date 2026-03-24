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


from src.validator.fhir_validator import FHIRValidator
from src.validator.agent import ValidatorAgent, ValidationDecision


class ClinicalAnalystAgent:
    """AC5: Agent that identifies, lookups, and extracts FHIR resources from clinical notes."""

    def __init__(
        self,
        mcp_client: Optional[FHIRDocClient] = None,
        nci_client: Optional[NCIClient] = None,
        validator: Optional[FHIRValidator] = None,
        validator_agent: Optional[ValidatorAgent] = None,
    ):
        self.mcp_client = mcp_client or FHIRDocClient()
        self.nci_client = nci_client or NCIClient()
        self.validator = validator or FHIRValidator()
        # Only initialize the ValidatorAgent if Anthropic is available
        self.validator_agent = (
            validator_agent
            if validator_agent
            else (ValidatorAgent() if settings.ANTHROPIC_API_KEY else None)
        )
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

    async def run(self, note: str, max_retries: int = 3) -> List[Any]:
        """AC2, AC4: Run the agent on a clinical note, with up to 3 retries via Validator feedback."""
        message_history = []
        attempt = 0

        while attempt <= max_retries:
            logger.info(
                f"--- Extraction Attempt {attempt + 1} of {max_retries + 1} ---"
            )
            try:
                # Use message history to allow LLM to see previous mistakes
                result = await self.agent.run(note, message_history=message_history)
                message_history = (
                    result.all_messages()
                )  # Save for next iteration if needed

                try:
                    extracted_data = json.loads(result.output.fhir_json_bundle)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode LLM output as JSON: {e}")
                    extracted_data = []  # Will likely trigger a validator rejection

                if not isinstance(extracted_data, list):
                    logger.error(
                        f"LLM returned a {type(extracted_data)} instead of a list."
                    )
                    extracted_data = []

                # 1. Python Validation (Tagging)
                logger.info("Python FHIRValidator evaluating schemas...")
                reports = self.validator.evaluate_bundle(extracted_data)

                # If no Validator Agent is configured, just use the Python validator's output directly (Fallback)
                if not self.validator_agent:
                    logger.warning(
                        "No ANTHROPIC_API_KEY found. Skipping Multi-Agent evaluation. Returning what Python validator accepted."
                    )
                    return [
                        r.resource
                        for r in reports
                        if r.status == "VALID" and r.resource is not None
                    ]

                # 2. Multi-Agent Evaluation (Claude)
                decision = await self.validator_agent.evaluate_bundle(
                    note=note,
                    extractor_messages=message_history,
                    validation_reports=reports,
                )

                if decision.accepted:
                    logger.info(
                        "VALIDATOR AGENT ACCEPTED THE BUNDLE. Extraction complete."
                    )
                    # Return only the resources that actually passed Python schema enforcement
                    return [
                        r.resource
                        for r in reports
                        if r.status == "VALID" and r.resource is not None
                    ]
                else:
                    logger.warning(
                        f"VALIDATOR AGENT REJECTED THE BUNDLE. Feedback:\n{decision.feedback}"
                    )
                    if attempt < max_retries:
                        # Append feedback as a new user message for the Extractor to try again
                        feedback_prompt = f"The Validator Agent rejected your extraction. Here is their feedback:\n{decision.feedback}\nPlease try again and output the completely fixed JSON array."
                        # Pydantic AI requires a string input here. We just append our feedback to the original note in our loop logic,
                        # but because we pass message_history, it knows what it just did. We update `note` to be the feedback.
                        note = feedback_prompt
                    attempt += 1

            except Exception as e:
                import traceback

                logger.error(f"Agent execution failed on attempt {attempt + 1}: {e}")
                logger.error(traceback.format_exc())
                attempt += 1

        logger.error(
            f"Extraction failed after {max_retries} retries. Returning whatever was valid on the last run."
        )
        return (
            [
                r.resource
                for r in reports
                if r.status == "VALID" and r.resource is not None
            ]
            if "reports" in locals()
            else []
        )
