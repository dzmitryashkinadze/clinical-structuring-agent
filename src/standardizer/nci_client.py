import logging
import httpx
from typing import Optional
from pydantic import BaseModel
from src.clinical_analyst.config import settings

logger = logging.getLogger(__name__)


class TerminologyMatch(BaseModel):
    """Represents a successfully resolved terminology concept."""

    system: str
    code: str
    display: str


class NCIClient:
    """AC1: Client for the National Cancer Institute (NCI) Enterprise Vocabulary Services (EVS) API."""

    BASE_URL = "https://api-evsrest.nci.nih.gov/api/v1/concept"

    # Map NCI terminologies to official FHIR URIs
    FHIR_SYSTEM_MAP = {
        "snomedct_us": "http://snomed.info/sct",
        "loinc": "http://loinc.org",
        "icd10cm": "http://hl7.org/fhir/sid/icd-10-cm",
        "ncit": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
    }

    async def search_concept(
        self, query: str, terminology: str = "snomedct_us"
    ) -> Optional[TerminologyMatch]:
        """AC2, AC4: Searches for a clinical concept and returns the best match."""
        url = f"{self.BASE_URL}/{terminology}/search"
        params = {
            "include": "minimal",
            "term": query,
            "type": "contains",  # Broader matching
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()
                concepts = data.get("concepts", [])

                if not concepts:
                    logger.debug(f"No matches found for '{query}' in {terminology}")
                    return None

                # Take the first (best) match
                best_match = concepts[0]

                # Resolve official FHIR system URI
                system_uri = self.FHIR_SYSTEM_MAP.get(terminology.lower(), terminology)

                logger.debug(
                    f"Found match for '{query}' in {terminology}: {best_match.get('code')}"
                )
                return TerminologyMatch(
                    system=system_uri,
                    code=best_match.get("code", ""),
                    display=best_match.get("name", ""),
                )

        except httpx.HTTPStatusError as e:
            # LOINC 404s are expected - NCI API limitation
            if e.response.status_code == 404 and terminology.lower() == "loinc":
                logger.debug(
                    f"LOINC lookup failed for '{query}' (expected - NCI API limitation)"
                )
            # SNOMED-CT 404s are unexpected
            elif e.response.status_code == 404:
                logger.warning(
                    f"Terminology lookup failed for '{query}' in {terminology}: {e.response.status_code}"
                )
            else:
                logger.error(f"NCI API HTTP error for '{query}' in {terminology}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"NCI API unexpected error for '{query}' in {terminology}: {e}"
            )
            return None
