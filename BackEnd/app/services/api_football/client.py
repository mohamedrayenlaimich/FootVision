import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class APIFootballError(Exception):
    """Base exception for API-Football errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


class APIFootballAuthError(APIFootballError):
    """Raised when authentication fails (missing or invalid x-apisports-key)."""
    pass


class APIFootballNotFoundError(APIFootballError):
    """Raised when requested resource is not found."""
    pass


class APIFootballRateLimitError(APIFootballError):
    """Raised when API rate limit / daily quota is reached."""
    pass


class APIFootballTimeoutError(APIFootballError):
    """Raised when API connection times out."""
    pass


class APIFootballClient:
    """
    Reusable client for API-Football (API-Sports v3 API).
    Authentication uses the x-apisports-key header (or x-rapidapi-key for RapidAPI endpoints).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 12.0,
    ):
        self.api_key = api_key or settings.API_FOOTBALL_KEY
        self.base_url = (base_url or settings.API_FOOTBALL_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        if "rapidapi" in self.base_url.lower():
            headers["x-rapidapi-key"] = self.api_key
            headers["x-rapidapi-host"] = "api-football-v1.p.rapidapi.com"
        else:
            headers["x-apisports-key"] = self.api_key
        return headers

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Asynchronously fetch data from API-Football.
        """
        if not self.api_key or self.api_key == "your_api_football_key_here":
            logger.warning("API_FOOTBALL_KEY is unconfigured or placeholder.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                return self._handle_response(response)
        except httpx.TimeoutException as err:
            logger.error(f"Timeout connecting to API-Football: {err}")
            raise APIFootballTimeoutError("API-Football request timed out", status_code=504) from err
        except httpx.RequestError as err:
            logger.error(f"Network error calling API-Football: {err}")
            raise APIFootballError(f"Network error connecting to API-Football: {str(err)}") from err

    def get_sync(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synchronously fetch data from API-Football.
        """
        if not self.api_key or self.api_key == "your_api_football_key_here":
            logger.warning("API_FOOTBALL_KEY is unconfigured or placeholder.")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=headers, params=params)
                return self._handle_response(response)
        except httpx.TimeoutException as err:
            logger.error(f"Timeout connecting to API-Football: {err}")
            raise APIFootballTimeoutError("API-Football request timed out", status_code=504) from err
        except httpx.RequestError as err:
            logger.error(f"Network error calling API-Football: {err}")
            raise APIFootballError(f"Network error connecting to API-Football: {str(err)}") from err

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        status_code = response.status_code

        if status_code not in (200, 201):
            if status_code in (401, 403):
                raise APIFootballAuthError(f"API-Football authentication failed ({status_code})", status_code=status_code)
            elif status_code == 404:
                raise APIFootballNotFoundError("API-Football resource not found", status_code=404)
            elif status_code == 429:
                raise APIFootballRateLimitError("API-Football rate limit exceeded", status_code=429)
            else:
                raise APIFootballError(f"API-Football HTTP Error {status_code}: {response.text}", status_code=status_code)

        data = response.json()

        # Check internal API-Football error fields
        errors = data.get("errors")
        if errors:
            if isinstance(errors, dict) and errors:
                err_msg = str(errors)
                if "token" in err_msg.lower() or "key" in err_msg.lower() or "auth" in err_msg.lower():
                    raise APIFootballAuthError(f"API-Football authentication error: {err_msg}", status_code=401, payload=data)
                elif "ratelimit" in err_msg.lower() or "requests" in err_msg.lower() or "quota" in err_msg.lower():
                    raise APIFootballRateLimitError(f"API-Football rate limit: {err_msg}", status_code=429, payload=data)
                else:
                    raise APIFootballError(f"API-Football error response: {err_msg}", status_code=status_code, payload=data)
            elif isinstance(errors, list) and len(errors) > 0:
                raise APIFootballError(f"API-Football errors: {errors}", status_code=status_code, payload=data)

        return data
