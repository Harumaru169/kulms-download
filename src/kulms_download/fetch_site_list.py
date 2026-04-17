from kulms_download.constants import *

import httpx
from collections.abc import Callable
from pprint import pp
import pickle
from pathlib import Path
import asyncio

from kulms_download.cookie_getter_window import *
from kulms_download.kulms_components import *

SITE_COLLECTION_URL = "https://lms.gakusei.kyoto-u.ac.jp/direct/site.json"
RESOURCE_JSON_URL_F_STR = "https://lms.gakusei.kyoto-u.ac.jp/direct/content/site/{}.json"

# すでにcookieが流し込まれたclientを想定している。
async def fetch_site_list(client: httpx.AsyncClient) -> list[Site]:
    sites_json_response = await client.get(SITE_COLLECTION_URL)
    sites_json_response.raise_for_status()
    site_list = json_to_sites(sites_json_response.text)
    
    for site in site_list:
        content_json_url = RESOURCE_JSON_URL_F_STR.format(site.id)
        content_json_response = await client.get(content_json_url)
        content_list = json_to_contents(content_json_response.text, site=site)
        
        # siteはcontentの一団を木構造とリストの両方で保持する。
        site.content_list = content_list
        _build_content_tree(site, content_list)
    
    return site_list

def _build_content_tree(site: Site, content_list: list[Content]):
    top_content = _pop_all(lambda c: c.url_essence=='', content_list)[0]
    site.top_content = top_content
    
    def recursive(target_content: Content):
        if not content_list: return #空っぽなら打ち切る
        children = _pop_all(lambda c: target_content.shouldHaveAsChild(c), content_list)
        target_content.children = children
        for child in children:
            recursive(child)
    
    recursive(top_content)

# TODO: ここは計算量的にまずいので頑張る
def _pop_all[T](predicate: Callable[[T], bool], list: list[T]) -> list[T]:
    """
    リストからpredicateに合致するすべての要素を削除し、削除した要素のリストを返す。
    """
    removed = [x for x in list if predicate(x)]
    list[:] = [x for x in list if not predicate(x)]
    return removed
