"""
Validator Agent for FHIR extraction quality assurance.

This module implements a secondary validation agent that acts as a supervisor
over the extraction pipeline, providing intelligent feedback for self-correction.

Main components:
- ValidationDecision: Pydantic model for validator output
- ValidatorAgent: Claude-based validation supervisor

Dependencies:
- Anthropic Claude: LLM for validation decisions
- pydantic-ai: Agent framework
"""

import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel

from src.clinical_analyst.config import settings
from src.utils.prompt_loader import load_prompt, PromptLoadError
from .fhir_validator import ValidationReport

logger = logging.getLogger(__name__)


class ValidationDecision(BaseModel):
    """
    Validation decision output from the supervisor agent.

    Contains the accept/reject decision and detailed feedback for
    the extraction agent to use in self-correction.

    Attributes:
        accepted: True if extraction is complete and valid, False otherwise
        feedback: Detailed correction instructions (empty if accepted)
    """

    accepted: bool = Field(
        description="True if the extracted bundle is perfect, False if corrections are needed."
    )
    feedback: str = Field(
        description="Detailed instructions on what the Extractor Agent missed or got wrong (based on the note and Pydantic errors). Empty if accepted."
    )


class ValidatorAgent:
    """
    Secondary validation agent that supervises FHIR extraction quality.

    Uses Claude Sonnet to evaluate extraction completeness and accuracy,
    comparing the extracted FHIR bundle against the original clinical note
    and Python validation results. Provides structured feedback for the
    extraction agent to self-correct.

    The validator checks for:
    - Missing clinical information from the note
    - FHIR schema validation errors
    - Hallucinated or incorrect data
    - Incomplete resource relationships

    Attributes:
        model: Claude model instance
        agent: Pydantic AI agent instance

    Example:
        >>> validator = ValidatorAgent()
        >>> decision = await validator.evaluate_bundle(note, messages, reports)
        >>> if not decision.accepted:
        ...     print(f"Issues found: {decision.feedback}")
    """

    def __init__(self) -> None:
        """
        Initialize the Validator Agent.

        Raises:
            ValueError: If required API key is not configured
            PromptLoadError: If the validator prompt cannot be loaded
        """
        # Initialize model based on provider selection
        if settings.VALIDATION_MODEL_PROVIDER == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY must be set in .env when VALIDATION_MODEL_PROVIDER=openai"
                )
            logger.debug(
                f"Initializing ValidatorAgent with OpenAI model={settings.OPENAI_VALIDATOR_MODEL_NAME}"
            )
            provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
            self.model = OpenAIChatModel(
                settings.OPENAI_VALIDATOR_MODEL_NAME, provider=provider
            )
        elif settings.VALIDATION_MODEL_PROVIDER == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY must be set in .env when VALIDATION_MODEL_PROVIDER=anthropic"
                )
            logger.debug(
                f"Initializing ValidatorAgent with Anthropic model={settings.CLAUDE_MODEL_NAME}"
            )
            provider = AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
            self.model = AnthropicModel(settings.CLAUDE_MODEL_NAME, provider=provider)
        else:
            raise ValueError(
                f"Invalid VALIDATION_MODEL_PROVIDER: {settings.VALIDATION_MODEL_PROVIDER}. Must be 'openai' or 'anthropic'"
            )

        # Load system prompt from file
        try:
            system_prompt = load_prompt("validator_supervisor", settings.PROMPTS_DIR)
            logger.debug(
                f"Loaded validator prompt (length: {len(system_prompt)} chars)"
            )
        except PromptLoadError as e:
            logger.error(f"Failed to load validator prompt: {e}")
            raise

        self.agent = Agent(
            self.model,
            output_type=ValidationDecision,
            system_prompt=system_prompt,
        )

    async def evaluate_bundle(
        self,
        note: str,
        extractor_messages: list,
        validation_reports: List[ValidationReport],
    ) -> ValidationDecision:
        """Phase 5 AC3: Consumes the context and generates a structured decision."""

        # Format the Pydantic validation status for the LLM prompt
        report_summary = []
        for i, report in enumerate(validation_reports):
            status = report.status
            res_type = report.raw_dict.get("resourceType", "Unknown")
            errors = ", ".join(report.errors) if report.errors else "None"

            block = f"Resource {i + 1} [{res_type}]: STATUS={status}\nErrors: {errors}\nRaw Data: {json.dumps(report.raw_dict, indent=2)}\n"
            report_summary.append(block)

        compiled_report = "\n".join(report_summary)

        prompt = (
            f"--- ORIGINAL CLINICAL NOTE ---\n{note}\n\n"
            f"--- PYTHON VALIDATION REPORT ---\n"
            f"The Extractor generated {len(validation_reports)} resources. Here is their evaluation against strict fhir.resources Python models:\n"
            f"{compiled_report}\n\n"
            "Review this output against the clinical note. Did they miss anything? Do they need to fix schema errors? Make your decision."
        )

        try:
            logger.info("Validator Agent evaluating bundle...")
            result = await self.agent.run(prompt)
            return result.output
        except Exception as e:
            logger.error(f"Validator Agent failed: {e}")
            # Failsafe: if the validator crashes, reject with a generic error
            return ValidationDecision(
                accepted=False,
                feedback=f"Validator Agent encountered a critical error: {e}",
            )
