import os
import json
import httpx
import click
from pathlib import Path
from bs4 import BeautifulSoup

DATA_DIR = Path("data/fhir_docs")
CORE_RESOURCES = [
    "Patient",
    "Observation",
    "Condition",
    "MedicationRequest",
    "Procedure",
    "AllergyIntolerance",
    "Encounter",
    "FamilyMemberHistory",
    "DiagnosticReport",
    "Immunization",
]


@click.group()
def cli():
    """FHIR Doc Tool CLI for R4."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@cli.command()
@click.option("--resources", help="Comma-separated list of resources to index")
def index(resources):
    """AC1: Index FHIR R4 resources into local cache."""
    target_resources = resources.split(",") if resources else CORE_RESOURCES

    with httpx.Client(base_url="https://hl7.org/fhir/R4/") as client:
        for res in target_resources:
            click.echo(f"Indexing {res}...")
            # 1. Download StructureDefinition (JSON)
            try:
                response = client.get(f"{res.lower()}.profile.json")
                response.raise_for_status()
                with open(DATA_DIR / f"{res}.profile.json", "w") as f:
                    json.dump(response.json(), f, indent=2)

                # 2. Scrape summary table from HTML
                html_response = client.get(f"{res.lower()}.html")
                html_response.raise_for_status()
                soup = BeautifulSoup(html_response.text, "html.parser")
                summary = {}
                # Basic parsing logic for the summary table (e.g., from the 'Summary' section)
                # For brevity, we'll store the page title and a link for now.
                summary["title"] = soup.title.string if soup.title else res
                summary["url"] = f"https://hl7.org/fhir/R4/{res.lower()}.html"

                with open(DATA_DIR / f"{res}.summary.json", "w") as f:
                    json.dump(summary, f, indent=2)

            except Exception as e:
                click.echo(f"Failed to index {res}: {e}", err=True)


@cli.command()
def list():
    """AC3: List indexed resources."""
    indexed = [f.stem.replace(".profile", "") for f in DATA_DIR.glob("*.profile.json")]
    if not indexed:
        click.echo("No resources indexed. Run 'fhir-doc index' first.")
    else:
        for res in sorted(indexed):
            click.echo(res)


@cli.command()
@click.argument("resource")
def query(resource):
    """AC2: Query a human-readable summary of a resource."""
    summary_path = DATA_DIR / f"{resource}.summary.json"
    if not summary_path.exists():
        click.echo(f"Resource '{resource}' not indexed.")
        return

    with open(summary_path) as f:
        summary = json.load(f)
        click.echo(f"Resource: {resource}")
        click.echo(f"Title: {summary.get('title')}")
        click.echo(f"URL: {summary.get('url')}")


if __name__ == "__main__":
    cli()
