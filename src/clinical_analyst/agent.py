"""
Clinical Analyst Agent for FHIR extraction.

This module implements the primary extraction agent that transforms unstructured
clinical notes into validated FHIR R4 resources. Uses Gemini 3 Flash with dynamic
schema lookup via MCP and integrates terminology standardization.

Main components:
- ExtractionResult: Pydantic model for agent output
- ClinicalAnalystAgent: Primary agent class with multi-agent validation loop

Dependencies:
- pydantic-ai: Agent framework
- Google Gemini: LLM for extraction
- MCP: Schema lookup
- NCI EVS: Terminology standardization
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
import json

from .config import settings
from .mcp_client import FHIRDocClient
from src.standardizer.nci_client import NCIClient
from src.validator.fhir_validator import FHIRValidator
from src.validator.agent import ValidatorAgent
from src.utils.prompt_loader import load_prompt, PromptLoadError

logger = logging.getLogger(__name__)


class ExtractionResult(BaseModel):
    """
    Result container for FHIR extraction output.

    The agent returns extracted FHIR resources as a JSON string
    to avoid issues with complex nested objects in Pydantic AI.

    Attributes:
        fhir_json_bundle: JSON string containing array of FHIR resources
    """

    fhir_json_bundle: str = Field(
        description="A JSON string representing an array of FHIR resources."
    )


class ClinicalAnalystAgent:
    """
    Primary extraction agent that transforms clinical notes into FHIR resources.

    Uses Gemini 3 Flash with dynamic schema lookup via MCP to extract
    structured FHIR data from unstructured clinical text. Integrates
    with terminology services for code standardization and includes
    a multi-agent validation loop for accuracy.

    The agent follows a "Lookup-then-Extract" flow:
    1. Lists available FHIR resource types via MCP
    2. Retrieves relevant schemas for identified resources
    3. Looks up standardized terminology codes
    4. Extracts and validates FHIR JSON
    5. Optionally uses Claude validator for quality assurance

    Attributes:
        mcp_client: Client for FHIR schema lookups via MCP
        nci_client: Client for terminology standardization (NCI EVS API)
        validator: Python FHIR validator for schema compliance
        validator_agent: Optional Claude-based validation supervisor
        model: Gemini model instance
        agent: Pydantic AI agent instance with registered tools

    Example:
        >>> agent = ClinicalAnalystAgent()
        >>> resources = await agent.run("Patient John Doe, 45yo, hypertensive")
        >>> print(f"Extracted {len(resources)} FHIR resources")
    """

    def __init__(
        self,
        mcp_client: Optional[FHIRDocClient] = None,
        nci_client: Optional[NCIClient] = None,
        validator: Optional[FHIRValidator] = None,
        validator_agent: Optional[ValidatorAgent] = None,
    ) -> None:
        """
        Initialize the Clinical Analyst Agent.

        Args:
            mcp_client: Optional pre-configured MCP client
            nci_client: Optional pre-configured NCI client
            validator: Optional pre-configured FHIR validator
            validator_agent: Optional pre-configured validation agent
        """
        self.mcp_client = mcp_client or FHIRDocClient()
        self.nci_client = nci_client or NCIClient()
        self.validator = validator or FHIRValidator()

        # Initialize ValidatorAgent if appropriate API key is available
        if validator_agent:
            self.validator_agent = validator_agent
        else:
            # Check if required API key is available for validation
            has_validator_key = (
                settings.VALIDATION_MODEL_PROVIDER == "openai"
                and settings.OPENAI_API_KEY
            ) or (
                settings.VALIDATION_MODEL_PROVIDER == "anthropic"
                and settings.ANTHROPIC_API_KEY
            )
            self.validator_agent = ValidatorAgent() if has_validator_key else None  # type: ignore[assignment]

        if not self.validator_agent:
            logger.info(
                "Validator agent disabled - validation loop will use Python-only validation"
            )

        # Initialize model based on provider selection
        if settings.EXTRACTION_MODEL_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is required when EXTRACTION_MODEL_PROVIDER=openai"
                )
            self.model = OpenAIChatModel(
                settings.OPENAI_MODEL_NAME,
                provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY),
            )
            logger.debug(
                f"Initializing ClinicalAnalystAgent with OpenAI model={settings.OPENAI_MODEL_NAME}"
            )
        elif settings.EXTRACTION_MODEL_PROVIDER == "google":
            if not settings.GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY is required when EXTRACTION_MODEL_PROVIDER=google"
                )
            self.model = GoogleModel(
                settings.GEMINI_MODEL_NAME,
                provider=GoogleProvider(api_key=settings.GOOGLE_API_KEY),
            )
            logger.debug(
                f"Initializing ClinicalAnalystAgent with Google model={settings.GEMINI_MODEL_NAME}"
            )
        elif settings.EXTRACTION_MODEL_PROVIDER == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY is required when EXTRACTION_MODEL_PROVIDER=anthropic"
                )
            self.model = AnthropicModel(
                settings.CLAUDE_MODEL_NAME,
                provider=AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY),
            )
            logger.debug(
                f"Initializing ClinicalAnalystAgent with Anthropic model={settings.CLAUDE_MODEL_NAME}"
            )
        else:
            raise ValueError(
                f"Invalid EXTRACTION_MODEL_PROVIDER: {settings.EXTRACTION_MODEL_PROVIDER}. Must be 'openai', 'google', or 'anthropic'"
            )

        # Load system prompt from file
        try:
            system_prompt = load_prompt("clinical_analyst", settings.PROMPTS_DIR)
            logger.debug(f"Loaded system prompt (length: {len(system_prompt)} chars)")
        except PromptLoadError as e:
            logger.error(f"Failed to load prompt: {e}")
            raise

        # Initialize agent with loaded prompt
        self.agent = Agent(
            self.model,
            output_type=ExtractionResult,
            system_prompt=system_prompt,
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
        message_history: List[Any] = []
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
