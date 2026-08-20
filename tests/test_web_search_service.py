import httpx
import pytest

from app.services import web_search_service
from app.services.web_search_service import (
    WebSearchConfigError,
    WebSearchError,
    search_web,
)


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", web_search_service.TAVILY_SEARCH_URL)
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    """Minimal stand-in for httpx.AsyncClient used as a context manager."""

    def __init__(self, response=None, raise_exc=None):
        self._response = response
        self._raise_exc = raise_exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def post(self, url, json=None):
        if self._raise_exc:
            raise self._raise_exc
        return self._response


@pytest.mark.asyncio
async def test_search_web_requires_api_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.web_search_service.get_settings",
        lambda: _settings(tavily_api_key=""),
    )

    with pytest.raises(WebSearchConfigError):
        await search_web("climate policy")


@pytest.mark.asyncio
async def test_search_web_success(monkeypatch):
    monkeypatch.setattr(
        "app.services.web_search_service.get_settings",
        lambda: _settings(tavily_api_key="fake-key"),
    )

    fake_response = _FakeResponse(
        {
            "results": [
                {"title": "A", "url": "https://a.com", "content": "content a"},
            ]
        }
    )
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda timeout=None: _FakeAsyncClient(response=fake_response)
    )

    results = await search_web("climate policy")
    assert results == [{"title": "A", "url": "https://a.com", "content": "content a"}]


@pytest.mark.asyncio
async def test_search_web_raises_on_timeout(monkeypatch):
    monkeypatch.setattr(
        "app.services.web_search_service.get_settings",
        lambda: _settings(tavily_api_key="fake-key"),
    )
    monkeypatch.setattr(
        "httpx.AsyncClient",
        lambda timeout=None: _FakeAsyncClient(
            raise_exc=httpx.TimeoutException("timed out")
        ),
    )

    with pytest.raises(WebSearchError):
        await search_web("climate policy")


@pytest.mark.asyncio
async def test_search_web_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.web_search_service.get_settings",
        lambda: _settings(tavily_api_key="fake-key"),
    )
    fake_response = _FakeResponse({}, status_code=500)
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda timeout=None: _FakeAsyncClient(response=fake_response)
    )

    with pytest.raises(WebSearchError):
        await search_web("climate policy")


@pytest.mark.asyncio
async def test_search_web_raises_on_malformed_response(monkeypatch):
    monkeypatch.setattr(
        "app.services.web_search_service.get_settings",
        lambda: _settings(tavily_api_key="fake-key"),
    )
    fake_response = _FakeResponse({"unexpected": "shape"})
    monkeypatch.setattr(
        "httpx.AsyncClient", lambda timeout=None: _FakeAsyncClient(response=fake_response)
    )

    with pytest.raises(WebSearchError):
        await search_web("climate policy")


def _settings(tavily_api_key: str):
    from app.config import Settings

    return Settings(
        tavily_api_key=tavily_api_key,
        web_search_max_results=5,
        web_search_timeout_seconds=15.0,
    )
