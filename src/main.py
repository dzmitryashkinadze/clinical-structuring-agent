import click
import asyncio
import json
import logging
from src.clinical_analyst.agent import ClinicalAnalystAgent
from src.validator.fhir_validator import FHIRValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("fhir_cli")


@click.group()
def cli():
    """Agentic EHR-to-FHIR Extraction Pipeline."""
    pass


@cli.command()
@click.option("--text", help="Raw clinical note text to process.", type=str)
@click.option(
    "--file",
    help="Path to a .txt or .md file containing the clinical note.",
    type=click.Path(exists=True, readable=True),
)
@click.option(
    "--out",
    help="Path to save the resulting FHIR JSON array (e.g. data/output/result.json).",
    type=click.Path(writable=True),
)
def process(text, file, out):
    """AC1, AC2, AC3: Extract FHIR resources from a single note."""

    if not text and not file:
        click.echo("Error: You must provide either --text or --file.", err=True)
        return

    if text and file:
        click.echo("Error: Please provide either --text OR --file, not both.", err=True)
        return

    note_content = ""
    if text:
        note_content = text
    else:
        with open(file, "r", encoding="utf-8") as f:
            note_content = f.read()

    # Create an event loop explicitly so click can run async code
    asyncio.run(run_pipeline(note_content, out))


async def run_pipeline(note: str, output_path: str):
    logger.info("Initializing Clinical Analyst Agent...")
    agent = ClinicalAnalystAgent()

    logger.info("Extracting resources from clinical note...")
    # The agent now handles validation internally, returning instantiated objects
    raw_resources = await agent.run(note)

    # We serialize the validated models to JSON strings, then parse to dicts for output
    json_output = [
        json.loads(res.model_dump_json(exclude_none=True)) for res in raw_resources
    ]

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2)
        logger.info(
            f"Successfully saved {len(json_output)} validated FHIR resources to {output_path}"
        )
    else:
        logger.info(
            f"Successfully extracted and validated {len(json_output)} FHIR resources:"
        )
        click.echo(json.dumps(json_output, indent=2))


if __name__ == "__main__":
    cli()
