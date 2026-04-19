from __future__ import annotations
from abc import ABC, abstractmethod

import asyncio, aiofiles, aiofiles.os, shutil
from pathlib import Path

from ..shared.components import Site, Resource
from ..shared.constants import Constants
from ..shared.api_client import AbstractApiClient

class AbstractResourceDownloader(ABC):
    @abstractmethod
    async def download_resources_for_site(self, site: Site, dest_dir: Path) -> None:
        pass
    
    @abstractmethod
    async def download_resources_for_site_list(self, site_list: list[Site], dest_dir: Path) -> None:
        pass


class ResourceDownloader(AbstractResourceDownloader):
    def __init__(self, client: AbstractApiClient, constants: Constants) -> None:
        self.client = client
        self.constants = constants
        self.semaphore = asyncio.Semaphore(self.constants.concurrent_download)
    
    # parent_dirの下にサイトリソースをダウンロードする。すでに同名のディレクトリがあるならそれを一旦削除してから。
    async def download_resources_for_site(self, site: Site, dest_dir: Path) -> None:
        if not site.root_resource:
            raise Exception
        top_dir_path = dest_dir / site.root_resource.title
        top_dir_already_exists = await aiofiles.os.path.exists(top_dir_path)
        if top_dir_already_exists:
            shutil.rmtree(top_dir_path)
        await self.__download_and_save_resource(site.root_resource, dest_dir)

    # 再帰関数なので、これをsite.top_resourceに対して呼ぶと、そのサイトの全てのファイルがディスクに書き込まれる。
    # resourceがフォルダならそのディレクトリを作って、その子供に対してもprocess_resourceを呼ぶ
    # resourceがファイルだったらダウンロードして保存する
    async def __download_and_save_resource(self, resource: Resource, parent_dir: Path):
        if resource.is_collection():
            dir_path = parent_dir / resource.title
            await aiofiles.os.makedirs(dir_path, exist_ok=True)
            
            async with asyncio.TaskGroup() as tg:
                for child in resource.children:
                    tg.create_task(self.__download_and_save_resource(child, dir_path))
        
        elif resource.is_weblink():
            # .urlファイルを生成
            filepath = (parent_dir / resource.title).with_suffix(".url")
            async with aiofiles.open(filepath, "w") as f:
                await f.write(f"[InternetShortcut]\nURL={resource.weblink_url}")
        
        else:
            url = resource.actualURL()
            filepath = parent_dir / resource.title
            
            async with self.semaphore:
                async with self.client.get_stream(url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=self.constants.chunk_bite_size):
                            await f.write(chunk)
    
    async def download_resources_for_site_list(self, site_list: list[Site], dest_dir: Path) -> None:
        async with asyncio.TaskGroup() as tg:
            for site in site_list:
                tg.create_task(self.download_resources_for_site(site, dest_dir))