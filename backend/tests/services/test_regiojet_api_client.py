import pytest
import httpx
import respx
from fastapi import HTTPException

from app.core.config import settings
from app.services.regiojet_api_client import (
    _fetch_regiojet_api,
    _fetch_regiojet_api_sync,
)

# Base URL for mocking
BASE_URL = settings.REGIOJET_API_BASE_URL


@pytest.mark.asyncio
class TestFetchRegiojetApiAsync:
    @respx.mock
    async def test_fetch_success(self):
        """Test successful API fetch."""
        endpoint = "/test-success"
        mock_response = {"status": "ok"}
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(200, json=mock_response))

        result = await _fetch_regiojet_api(endpoint)
        assert result == mock_response

    @respx.mock
    async def test_fetch_raises_504_on_timeout(self):
        """Test that a TimeoutException is caught and re-raised as HTTPException 504."""
        endpoint = "/test-timeout"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_regiojet_api(endpoint)
        assert exc_info.value.status_code == 504

    @respx.mock
    async def test_fetch_raises_503_on_request_error(self):
        """Test that a RequestError is caught and re-raised as HTTPException 503."""
        endpoint = "/test-request-error"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=httpx.RequestError("Request Error"))

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_regiojet_api(endpoint)
        assert exc_info.value.status_code == 503

    @respx.mock
    async def test_fetch_raises_400_on_status_400(self):
        """Test that a 400 status error is re-raised as HTTPException 400."""
        endpoint = "/test-400"
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(400, json={"detail": "Bad Request"}))

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_regiojet_api(endpoint)
        assert exc_info.value.status_code == 400

    @respx.mock
    async def test_fetch_raises_502_on_other_status_error(self):
        """Test that a non-400 status error (e.g., 500) is re-raised as HTTPException 502."""
        endpoint = "/test-500"
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(500, json={"detail": "Server Error"}))

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_regiojet_api(endpoint)
        assert exc_info.value.status_code == 502

    @respx.mock
    async def test_fetch_raises_500_on_generic_exception(self):
        """Test that a generic exception is caught and re-raised as HTTPException 500."""
        endpoint = "/test-generic-exception"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=Exception("Generic Error"))

        with pytest.raises(HTTPException) as exc_info:
            await _fetch_regiojet_api(endpoint)
        assert exc_info.value.status_code == 500


class TestFetchRegiojetApiSync:
    @respx.mock
    def test_fetch_sync_success(self):
        """Test successful synchronous API fetch."""
        endpoint = "/test-sync-success"
        mock_response = {"status": "ok"}
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(200, json=mock_response))

        result = _fetch_regiojet_api_sync(endpoint)
        assert result == mock_response

    @respx.mock
    def test_fetch_sync_raises_504_on_timeout(self):
        """Test that a TimeoutException is caught and re-raised as HTTPException 504 in sync."""
        endpoint = "/test-sync-timeout"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(HTTPException) as exc_info:
            _fetch_regiojet_api_sync(endpoint)
        assert exc_info.value.status_code == 504

    @respx.mock
    def test_fetch_sync_raises_503_on_request_error(self):
        """Test that a RequestError is caught and re-raised as HTTPException 503 in sync."""
        endpoint = "/test-sync-request-error"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=httpx.RequestError("Request Error"))

        with pytest.raises(HTTPException) as exc_info:
            _fetch_regiojet_api_sync(endpoint)
        assert exc_info.value.status_code == 503

    @respx.mock
    def test_fetch_sync_raises_400_on_status_400(self):
        """Test that a 400 status error is re-raised as HTTPException 400 in sync."""
        endpoint = "/test-sync-400"
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(400, json={"detail": "Bad Request"}))

        with pytest.raises(HTTPException) as exc_info:
            _fetch_regiojet_api_sync(endpoint)
        assert exc_info.value.status_code == 400

    @respx.mock
    def test_fetch_sync_raises_502_on_other_status_error(self):
        """Test that a non-400 status error (e.g., 500) is re-raised as HTTPException 502 in sync."""
        endpoint = "/test-sync-500"
        respx.get(f"{BASE_URL}{endpoint}").mock(return_value=httpx.Response(500, json={"detail": "Server Error"}))

        with pytest.raises(HTTPException) as exc_info:
            _fetch_regiojet_api_sync(endpoint)
        assert exc_info.value.status_code == 502

    @respx.mock
    def test_fetch_sync_raises_500_on_generic_exception(self):
        """Test that a generic exception is caught and re-raised as HTTPException 500 in sync."""
        endpoint = "/test-sync-generic-exception"
        respx.get(f"{BASE_URL}{endpoint}").mock(side_effect=Exception("Generic Error"))

        with pytest.raises(HTTPException) as exc_info:
            _fetch_regiojet_api_sync(endpoint)
        assert exc_info.value.status_code == 500
