from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

CONTENT_URL_PREFIX = "https://lms.gakusei.kyoto-u.ac.jp/access/content/group/"
CONTENT_CONTAINER_PREFIX = "/content/group/"


@dataclass
class Resource:
    site: Site
    title: str
    type: str
    url_essence: str  # jsonのurlフィールドから、site-id/までの冗長な部分を抜いたもの
    container_essence: str  # 上と同様
    children: list[Resource]
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
            weblink_url=dict.get("webLinkUrl"),
        )

    def is_collection(self) -> bool:
        return self.type == "collection"

    def is_weblink(self) -> bool:
        return self.type == "text/url"

    # 意味論において、selfがresourceを子として持つかどうか判定
    def shouldHaveAsChild(self, resource: Resource) -> bool:
        return resource.container_essence == self.url_essence

    def actualURL(self) -> str:
        return f"https://lms.gakusei.kyoto-u.ac.jp/access/content/group/{self.site.id}/{self.url_essence}"


@dataclass
class Site:
    title: str
    id: str
    site_owner_name: str
    root_resource: Resource | None
    resource_list: list[Resource]

    @classmethod
    def from_dict(cls, dict):
        return cls(
            id=dict.get("id"),
            title=dict.get("title"),
            site_owner_name=dict.get("siteOwner").get("userDisplayName"),
            root_resource=None,
            resource_list=[],
        )
