"""
Root conftest.py for FootVision tests.
Adds BackEnd/ to sys.path so `app` and `main` can be imported from any test.
"""
import sys
import os

# Add the BackEnd directory to sys.path so imports like `from app...` and `from main import app` work
_backend_dir = os.path.join(os.path.dirname(__file__), "..", "BackEnd")
_backend_dir = os.path.abspath(_backend_dir)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_api_football_cache():
    """Prevent the API-Football TTL cache from leaking responses between tests."""
    from app.services.api_football import client as api_client

    api_client._CACHE.clear()
    yield
    api_client._CACHE.clear()
