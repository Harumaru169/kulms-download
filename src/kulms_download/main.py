from kulms_download.constants import *
from pathlib import Path
import asyncio, questionary, httpx
from questionary import Choice
from rich.console import Console
import platformdirs

from kulms_download.kulms_components import *
from kulms_download.download import *
from kulms_download.secrets_get_set import set_secrets, delete_secrets
from kulms_download.settings import shared_settings
from kulms_download.cookie_persistence import remove_cookies_file

async def download_cli(console: Console):
    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT) as client:
        with console.status("サイト情報を取得中..."):
            client.cookies = get_cookie_jar()
            site_list = await fetch_site_list(client)
        
        selected_site_list = await questionary.checkbox(
            "資料をダウンロードしたいサイトをすべて選択:",
            choices=list(map(lambda s: Choice(s.title, s), site_list))
        ).ask_async()
        
        dest_dir = Path(
            await questionary.path(
            "ダウンロード先のディレクトリパスを入力:",
            default=platformdirs.user_downloads_dir()
            ).ask_async()
        )
        if not dest_dir.exists():
            raise Exception
        
        confirmation = await questionary.confirm("ダウンロードを開始しますか？").ask_async()
        if not confirmation:
            print("中止します。")
            return
        
        semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOAD)
        with console.status("ダウンロード中..."):
            async with asyncio.TaskGroup() as tg:
                for site in selected_site_list:
                    tg.create_task(download_site_resources(site, dest_dir, client, semaphore))
        print("ダウンロードが完了しました")

async def settings_cli(console: Console):
    choices = [
        Choice("Cookieの削除", delete_cookie_cli),
        Choice("自動入力するECS-IDとパスワードの保存/削除", password_setting_cli),
        Choice("認証画面でパスワード管理アプリを自動で開く", open_app_setting_cli)
    ]
    
    next_func = await questionary.select("=== 設定 ===", choices=choices).ask_async()
    await next_func(console)

async def delete_cookie_cli(console: Console):
    print("Cookieデータはログイン後、1時間程度保持されています。削除すると、次回使用時にログインウインドウが立ち上がります。")
    confirmation = await questionary.confirm("Cookieデータを削除しますか？").ask_async()
    if not confirmation:
        print("中止しました。")
        return
    remove_cookies_file()
    print("Cookieデータを削除しました。")


async def password_setting_cli(console: Console):
    num = await questionary.select(
        "=== 自動入力するECS-IDとパスワードの保存/削除 ===", 
        choices=[
            Choice("更新,追加", 0),
            Choice("削除", 1)
        ]
    ).ask_async()
    
    if num == 0:
        username = await questionary.password("ESC-IDのユーザー名を入力:").ask_async()
        password = await questionary.password("ESC-IDのパスワードを入力:").ask_async()
        set_secrets(username, password)
        print("パスワードの設定が完了しました。")
    elif num == 1:
        delete_secrets()
        print("パスワードを削除しました。")        

async def open_app_setting_cli(console: Console):
    print("KULMSのログインウインドウが起動した時に、設定することで同時にパスワード管理アプリを起動させることができます。ワンタイムパスワードの入力がスムーズにできて便利です。")
    
    num = await questionary.select(
        "",
        choices=[
            Choice("パスワード管理アプリの登録", 0),
            Choice("パスワード管理アプリを起動しないようにする", 1)
        ]
    ).ask_async()
    
    if num == 0:
        validate = lambda path_str: True if Path(path_str).exists() else "指定されたパスにアプリケーションが存在しません。"
        path_str = await questionary.path(
            "アプリケーションのパスを入力:",
            default=platformdirs.site_applications_dir(),
            validate=validate
        ).ask_async()
        shared_settings.password_app_executable_path = path_str
        print("アプリケーションの設定が完了しました。")
    elif num == 1:
        shared_settings.password_app_executable_path = None
        print("パスワード管理アプリを起動しないようにしました。")

async def entry_point():
    console = Console()
    
    choices = [
        Choice("サイトリソースのダウンロード", download_cli),
        Choice("設定", settings_cli)
    ]
    
    cli_func = await questionary.select("=== KULMS Download ===", choices=choices).ask_async()
    await cli_func(console)

def main():
    asyncio.run(entry_point())

if __name__ == "__main__":
    main()