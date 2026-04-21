from __future__ import annotations
from collections.abc import Callable
from typing import cast, AsyncContextManager
from abc import ABC, abstractmethod

import httpx, asyncio, json

from .components import Site, Resource
from .constants import Constants
from .exceptions import NetworkError
from ..cookie.cookie_fetcher import AbstractCookieFetcher

class AbstractApiClient(ABC):
    @abstractmethod
    async def __aenter__(self):
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        pass
    
    @abstractmethod
    def get_cookie(self) -> None:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def fetch_partial_site_list_without_resource(self, page_size: int, offset: int) -> list[Site]:
        pass
    
    @abstractmethod
    async def fetch_resource_list(self, site: Site) -> list[Resource]:
        pass

    @abstractmethod
    def get_stream(self, url: str) -> AsyncContextManager[httpx.Response]:
        pass

# httpx.AsyncClientを内部に包んでいる
class ApiClient(AbstractApiClient):
    def __init__(self, cookie_fetcher: AbstractCookieFetcher, constants: Constants) -> None:
        super().__init__()
        self.cookie_fetcher = cookie_fetcher
        self.constants = constants
        self.http_client = httpx.AsyncClient(timeout=self.constants.download_timeout)
    
    # clientを使ってデータを取得する前にこれを少なくとも1回呼ばなければならない。
    def get_cookie(self) -> None:
        jar = self.cookie_fetcher.fetch()
        self.http_client.cookies = jar.to_httpx_cookies()
    
    async def close(self) -> None:
        await self.http_client.aclose()
    
    async def __aenter__(self) -> ApiClient:
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
    
    # offsetは0始まり
    def _site_list_json_url(self, page_size: int, offset: int) -> str:
        return f"https://lms.gakusei.kyoto-u.ac.jp/direct/site.json?_limit={page_size}&_start={offset}"
    
    def _resource_list_json_url(self, site: Site) -> str:
        return f"https://lms.gakusei.kyoto-u.ac.jp/direct/content/site/{site.id}.json"
    
    async def fetch_partial_site_list_without_resource(self, page_size: int, offset: int) -> list[Site]:
        try:
            response = await self.http_client.get(self._site_list_json_url(page_size, offset))
            response.raise_for_status()
            collection = response.json().get("site_collection", [])
            return [Site.from_dict(item) for item in collection]
        except httpx.HTTPError as e:
            raise NetworkError("サイト一覧の取得に失敗しました") from e
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise NetworkError("サイト一覧のJSON解析に失敗しました") from e
    
    async def fetch_resource_list(self, site: Site) -> list[Resource]:
        try:
            url = self._resource_list_json_url(site)
            response = await self.http_client.get(url)
            response.raise_for_status()
            collection = response.json().get("content_collection", [])
            
            url_prefix = f"https://lms.gakusei.kyoto-u.ac.jp/access/content/group/{site.id}/"
            container_prefix = f"/content/group/{site.id}/"
            return [Resource.from_dict(item, site, url_prefix, container_prefix) for item in collection]
        except httpx.HTTPError as e:
            raise NetworkError(f"リソース一覧の取得に失敗しました: {site.title}") from e
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise NetworkError(f"リソース一覧のJSON解析に失敗しました: {site.title}") from e
    
    def get_stream(self, url: str) -> AsyncContextManager[httpx.Response]:
        return self.http_client.stream("GET", url)