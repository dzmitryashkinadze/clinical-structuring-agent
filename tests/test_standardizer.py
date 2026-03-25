import pytest
from src.standardizer.nci_client import NCIClient, TerminologyMatch


@pytest.mark.asyncio
async def test_nci_client_success(mocker):
    """AC1, AC2: Verify successful search returns a TerminologyMatch."""
    # We will use httpx in the client, so we mock httpx.AsyncClient.get
    mock_get = mocker.patch("httpx.AsyncClient.get")

    # Mocking the NCI EVS API response format
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "concepts": [
            {
                "code": "38341003",
                "name": "Hypertensive disorder, systemic arterial",
                "terminology": "snomedct_us",
            }
        ]
    }
    mock_get.return_value = mock_response

    client = NCIClient()
    result = await client.search_concept("Hypertension", "snomedct_us")

    assert isinstance(result, TerminologyMatch)
    assert result.code == "38341003"
    assert result.display == "Hypertensive disorder, systemic arterial"
    assert (
        result.system == "http://snomed.info/sct"
    )  # Should map snomedct_us to the official FHIR URI


@pytest.mark.asyncio
async def test_nci_client_not_found(mocker):
    """AC4: Verify empty response returns None."""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"concepts": []}
    mock_get.return_value = mock_response

    client = NCIClient()
    result = await client.search_concept("MadeUpDisease123", "snomedct_us")

    assert result is None


@pytest.mark.asyncio
async def test_nci_client_http_error(mocker):
    """AC4: Verify HTTP errors are caught gracefully."""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
    mock_get.return_value = mock_response

    client = NCIClient()
    result = await client.search_concept("Hypertension", "snomedct_us")

    assert result is None
