from kulms_download.constants import *

import asyncio
import aiofiles, aiofiles.os, shutil
import httpx
from pathlib import Path
from urllib.parse import urljoin
from kulms_download.kulms_components import *
from datetime import datetime, timezone

from kulms_download.cookie_getter_window import employ_window_worker_and_get_cookie_jar
from kulms_download.cookie_coding import *
from kulms_download.cookie_persistence import *
from kulms_download.fetch_site_list import fetch_site_list

# parent_dirの下にサイトリソースをダウンロードする。すでに同名のディレクトリがあるならそれを一旦削除してから。
async def download_site_resources(site: Site, parent_dir: Path, client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    if not site.top_content:
        raise Exception
    top_dir_path = parent_dir / site.top_content.title
    top_dir_already_exists = await aiofiles.os.path.exists(top_dir_path)
    if top_dir_already_exists:
        shutil.rmtree(top_dir_path)
    await __download_and_save_content(site.top_content, parent_dir, client, semaphore)

# 再帰関数なので、これをsite.top_contentに対して呼ぶと、そのサイトの全てのファイルがディスクに書き込まれる。
# contentがフォルダならそのディレクトリを作って、その子供に対してもprocess_contentを呼ぶ
# contentがファイルだったらダウンロードして保存する
async def __download_and_save_content(content: Content, parent_dir: Path, client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    if content.is_collection():
        dir_path = parent_dir / content.title
        await aiofiles.os.makedirs(dir_path, exist_ok=True)
        
        async with asyncio.TaskGroup() as tg:
            for child in content.children:
                # 再帰呼び出し
                tg.create_task(__download_and_save_content(child, dir_path, client, semaphore))
    elif content.is_weblink():
        # .urlファイルを生成
        filepath = (parent_dir / content.title).with_suffix(".url")
        async with aiofiles.open(filepath, "w") as f:
            await f.write(f"[InternetShortcut]\nURL={content.weblink_url}")
    else:
        url = content.actualURL()
        filepath = parent_dir / content.title
        
        # httpxでの非同期ストリーム取得
        async with semaphore:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                
                # 注意: ここのopen()はブロッキングI/O
                async with aiofiles.open(filepath, 'wb') as f:
                    # チャンクごとに非同期イテレート
                    async for chunk in response.aiter_bytes(chunk_size=CHUNK_BITE_SIZE):
                        await f.write(chunk)


# クッキーの保存、有効期限による破棄の判断などもやる
def get_cookie_jar() -> httpx.Cookies:
    saved = load_cookies_and_expiration_dt_from_file()
    if (saved is None) or (saved[1] < datetime.now(timezone.utc)):
        # 新鮮なクッキーを仕入れる。それをファイルに保存して、returnする。
        cookies, expiration_date = employ_window_worker_and_get_cookie_jar()
        if expiration_date is None:
            expiration_date = datetime.now() + DEFAULT_COOKIE_EXPIRATION
        save_cookies_and_expiration_dt_to_file(cookies, expiration_date)
        return cookies_to_jar(cookies)
    else:
        return cookies_to_jar(saved[0])

async def __download_test():
    site_list: list[Site] = []
    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT) as client:
        client.cookies = get_cookie_jar()
        site_list = await fetch_site_list(client)
            
        dest_dir = Path("/Users/kharuyama/Downloads/")
        # semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOAD)
        # await download_and_save_content(site.top_content, dest_dir, client, semaphore)
        print("downloaded. everything OK.")

if __name__ == "__main__":
    asyncio.run(__download_test())