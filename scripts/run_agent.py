import asyncio
import sys
import logging
import logfire
from pathlib import Path
from src.clinical_analyst.agent import ClinicalAnalystAgent
from src.clinical_analyst.config import settings

# Configure logfire to output to console
logfire.configure(send_to_logfire=False)
logfire.instrument_pydantic()

# Configure logging to see what the agent is doing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_agent")


async def main():
    if not settings.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not set in the environment or .env file.")
        sys.exit(1)

    agent = ClinicalAnalystAgent()

    sample_note = "Patient John Doe, a 45-year-old male, was seen today for a routine checkup. He has a history of hypertension. Blood pressure today was 130/80."
    logger.info("Running agent on sample clinical note...")
    logger.info(f"Note content:\n{sample_note}\n")

    try:
        resources = await agent.run(sample_note)
        logger.info(
            f"Successfully validated and instantiated {len(resources)} FHIR resources:"
        )
        for res in resources:
            logger.info(res.json(indent=2))

    except Exception as e:
        logger.error(f"Error running agent: {e}")


if __name__ == "__main__":
    asyncio.run(main())
