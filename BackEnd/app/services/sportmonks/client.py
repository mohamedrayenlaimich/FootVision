import logging
import time
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("sportmonks.client")

# Simple in-memory cache: (cache_key) -> (timestamp, data)
_CACHE: Dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 30  # 30 seconds for live/calendar queries


class SportmonksClient:
    """
    HTTP client for Sportmonks Football API v3.
    Supports token authentication, automatic include handling, and in-memory TTL caching.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 12.0,
    ):
        self.api_token = api_token or settings.SPORTMONKS_API_TOKEN
        self.base_url = (base_url or settings.SPORTMONKS_BASE_URL).rstrip("/")
        # Root v3 base for endpoints like /my/leagues
        self.root_v3_url = "https://api.sportmonks.com/v3"
        self.timeout = timeout

    def _get_cache_key(self, endpoint: str, params: Optional[Dict[str, Any]]) -> str:
        param_str = "&".join(f"{k}={v}" for k, v in sorted((params or {}).items()))
        return f"{endpoint}?{param_str}"

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        includes: Optional[list[str]] = None,
        use_cache: bool = True,
        ttl_seconds: int = CACHE_TTL_SECONDS,
        use_root_v3: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform an authenticated GET request to Sportmonks API v3.
        """
        request_params = dict(params or {})
        request_params["api_token"] = self.api_token

        if includes:
            request_params["include"] = ";".join(includes)

        cache_key = self._get_cache_key(endpoint, request_params)
        now = time.time()

        if use_cache and cache_key in _CACHE:
            cached_time, cached_data = _CACHE[cache_key]
            if now - cached_time < ttl_seconds:
                logger.debug("Sportmonks cache hit for %s", endpoint)
                return cached_data

        base = self.root_v3_url if use_root_v3 else self.base_url
        clean_endpoint = endpoint.lstrip("/")
        url = f"{base}/{clean_endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=request_params)
                response.raise_for_status()
                data = response.json()

                if use_cache:
                    _CACHE[cache_key] = (now, data)

                return data

        except httpx.HTTPStatusError as e:
            logger.error("Sportmonks API HTTP %s: %s", e.response.status_code, e.response.text)
            try:
                err_json = e.response.json()
                msg = err_json.get("message", str(e))
            except Exception:
                msg = str(e)
            raise RuntimeError(f"Sportmonks API error ({e.response.status_code}): {msg}")
        except httpx.RequestError as e:
            logger.error("Sportmonks API connection error: %s", e)
            raise RuntimeError(f"Sportmonks API connection failure: {str(e)}")


# Singleton instance for general use
sportmonks_client = SportmonksClient()
