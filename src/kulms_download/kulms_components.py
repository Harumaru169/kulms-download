from __future__ import annotations
from dataclasses import dataclass
import json
import urllib.parse

CONTENT_URL_PREFIX = "https://lms.gakusei.kyoto-u.ac.jp/access/content/group/"
CONTENT_CONTAINER_PREFIX = "/content/group/"

@dataclass
class Content:
    site: Site
    title: str
    type: str
    url_essence: str # jsonのurlフィールドから、site-id/までの冗長な部分を抜いたもの
    container_essence: str # 上と同様
    children: list[Content]
    weblink_url: str
    
    @classmethod
    def from_dict(cls, dict, site: Site, url_prefix: str, container_prefix: str):
        url_essence = urllib.parse.unquote(dict.get("url")).removeprefix(url_prefix)
        container_essence = dict.get("container").removeprefix(container_prefix)
        
        return cls(
            site=site,
            title=dict.get("title"),
            type=dict.get("type"),
            url_essence=url_essence,
            container_essence=container_essence,
            children=[],
            weblink_url=dict.get("webLinkUrl")
        )
    
    def is_collection(self) -> bool:
        return self.type == "collection"
    
    def is_weblink(self) -> bool:
        return self.type ==  "text/url"
    
    # 意味論において、selfがcontentを子として持つかどうか判定
    def shouldHaveAsChild(self, content: Content) -> bool:
        return content.container_essence == self.url_essence
    
    def actualURL(self) -> str:
        return f"https://lms.gakusei.kyoto-u.ac.jp/access/content/group/{self.site.id}/{self.url_essence}"

def json_to_contents(json_str: str, site: Site) -> list[Content]:
    data = json.loads(json_str)
    collection = data.get("content_collection", [])
    
    url_prefix = f"https://lms.gakusei.kyoto-u.ac.jp/access/content/group/{site.id}/"
    container_prefix = f"/content/group/{site.id}/"
    return [Content.from_dict(item, site, url_prefix, container_prefix) for item in collection]
    
        

@dataclass
class Site:
    title: str
    id: str
    site_owner_name: str
    top_content: Content | None
    content_list: list[Content]
    
    @classmethod
    def from_dict(cls, dict):
        return cls(
            id=dict.get("id"),
            title=dict.get("title"),
            site_owner_name=dict.get("siteOwner").get("userDisplayName"),
            top_content=None,
            content_list=[]
        )
    
    def resources_json_url(self) -> str:
        return "https://lms.gakusei.kyoto-u.ac.jp/direct/content/site/{}.json".format(self.id)

def json_to_sites(json_str: str) -> list[Site]:
    data = json.loads(json_str)
    collection = data.get("site_collection", [])
    return [Site.from_dict(item) for item in collection]