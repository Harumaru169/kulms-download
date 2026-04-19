from __future__ import annotations
from collections.abc import Callable
from typing import cast
from abc import ABC, abstractmethod

from ..shared.components import Site, Resource
from ..shared.constants import Constants
from ..shared.api_client import AbstractApiClient

class AbstractMetadataFetcher(ABC):
    @abstractmethod
    async def fetch_site_list(self) -> list[Site]:
        pass

class MetadataFetcher(AbstractMetadataFetcher):
    def __init__(self, client: AbstractApiClient) -> None:
        self.client = client
    
    async def fetch_site_list(self) -> list[Site]:
        site_list = await self.client.fetch_site_list_without_resource()
        
        # TODO: make this loop concurrent
        for site in site_list:
            resource_list = await self.client.fetch_resource_list(site)
            site.resource_list = resource_list
            self._build_resource_tree(site, resource_list)
        return site_list
    
    @classmethod
    def _build_resource_tree(cls, site: Site, resource_list: list[Resource]):
        root_resource = cls._pop_all(lambda c: c.url_essence=='', resource_list)[0]
        site.root_resource = root_resource
        
        def recursive(target_content: Resource):
            if not resource_list: return #空っぽなら打ち切る
            children = cls._pop_all(lambda c: target_content.shouldHaveAsChild(c), resource_list)
            target_content.children = children
            for child in children:
                recursive(child)
        
        recursive(root_resource)

    # TODO: ここは計算量的にまずいので頑張る
    # リストからpredicateに合致するすべての要素を削除し、削除した要素のリストを返す。
    @classmethod
    def _pop_all[T](cls, predicate: Callable[[T], bool], list: list[T]) -> list[T]:
        removed = [x for x in list if predicate(x)]
        list[:] = [x for x in list if not predicate(x)]
        return removed
