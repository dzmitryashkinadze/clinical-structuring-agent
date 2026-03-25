"""
CLI interface for the FHIR structuring agent.

This module provides command-line access to the FHIR extraction pipeline,
allowing processing of clinical notes from text or files.

Commands:
- process: Extract FHIR resources from clinical notes

Usage:
    python -m src.main process --text "Patient John Doe..."
    python -m src.main process --file data/notes/note.txt --out output.json
"""

import click
import asyncio
import json
import logging
from typing import Optional

from src.clinical_analyst.agent import ClinicalAnalystAgent
from src.utils.logging_config import setup_logging

# Setup logging once at module load
setup_logging()
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
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
def process(text: Optional[str], file: Optional[str], out: Optional[str]) -> None:
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
        with open(file, "r", encoding="utf-8") as f:  # type: ignore
            note_content = f.read()

    # Create an event loop explicitly so click can run async code
    asyncio.run(run_pipeline(note_content, out))


async def run_pipeline(note: str, output_path: Optional[str]) -> None:
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
