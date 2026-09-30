import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FootballDataAPIError(Exception):
    """Base exception for Football Data API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class FootballDataAuthError(FootballDataAPIError):
    """Raised when authentication fails (401/403 or missing API key)."""
    pass


class FootballDataNotFoundError(FootballDataAPIError):
    """Raised when requested resource is not found (404)."""
    pass


class FootballDataRateLimitError(FootballDataAPIError):
    """Raised when API rate limit is exceeded (429)."""
    pass


class FootballDataTimeoutError(FootballDataAPIError):
    """Raised when API request times out."""
    pass


class FootballDataClient:
    """
    Reusable API client for football-data.org (v4 API).
    Authentication is handled via the X-Auth-Token HTTP header.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key or settings.FOOTBALL_DATA_API_KEY
        self.base_url = (base_url or settings.FOOTBALL_DATA_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-Auth-Token"] = self.api_key
        return headers

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Asynchronously fetch data from a given football-data.org API endpoint.
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.warning("FOOTBALL_DATA_API_KEY is not set or using default placeholder.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                return self._handle_response(response)
        except httpx.TimeoutException as err:
            logger.error(f"Timeout connecting to Football-Data API: {err}")
            raise FootballDataTimeoutError("Football-Data API request timed out", status_code=504) from err
        except httpx.RequestError as err:
            logger.error(f"HTTP request error: {err}")
            raise FootballDataAPIError(f"Network error connecting to Football-Data API: {str(err)}") from err

    def get_sync(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synchronously fetch data from a given football-data.org API endpoint.
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.warning("FOOTBALL_DATA_API_KEY is not set or using default placeholder.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                return self._handle_response(response)
        except httpx.TimeoutException as err:
            logger.error(f"Timeout connecting to Football-Data API: {err}")
            raise FootballDataTimeoutError("Football-Data API request timed out", status_code=504) from err
        except httpx.RequestError as err:
            logger.error(f"HTTP request error: {err}")
            raise FootballDataAPIError(f"Network error connecting to Football-Data API: {str(err)}") from err

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        status_code = response.status_code

        if status_code == 200:
            return response.json()

        try:
            error_json = response.json()
            message = error_json.get("message", response.text)
        except Exception:
            error_json = None
            message = response.text or f"HTTP Error {status_code}"

        if status_code in (401, 403):
            raise FootballDataAuthError(f"Authentication failed: {message}", status_code=status_code, payload=error_json)
        elif status_code == 404:
            raise FootballDataNotFoundError(f"Resource not found: {message}", status_code=status_code, payload=error_json)
        elif status_code == 429:
            raise FootballDataRateLimitError(f"Rate limit exceeded: {message}", status_code=status_code, payload=error_json)
        else:
            raise FootballDataAPIError(f"Football-Data API error ({status_code}): {message}", status_code=status_code, payload=error_json)
