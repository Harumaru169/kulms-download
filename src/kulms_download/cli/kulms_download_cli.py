from kulms_download.shared.constants import Constants
from pathlib import Path
import asyncio, questionary, httpx
from questionary import Choice
from rich.console import Console
import platformdirs
from datetime import timedelta

from ..shared.components import Site, Resource
from ..shared.settings import Settings
from ..shared.api_client import ApiClient
from ..cookie.credential_manager import CredentialManager
from ..cookie.password_app_opener import PasswordAppOpener
from ..cookie.remote_cookie_fetcher import RemoteCookieFetcher
from ..cookie.local_cookie_manager import LocalCookieManager
from ..cookie.cookie_fetcher import CookieFetcher
from ..metadatafetch.metadata_fetcher import MetadataFetcher
from ..download.resource_downloader import ResourceDownloader
from ..shared.exceptions import *

def main():
    kulms_download_cli = KulmsDownloadCli()
    try:
        asyncio.run(kulms_download_cli.main())
    except KeyboardInterrupt:
        print("中断しました")
    except KulmsDownloadError as e:
        kulms_download_cli.console.print(
            f"エラー: {kulms_download_cli._user_message_for_error(e)}"
        )
    except Exception:
        kulms_download_cli.console.print(
            "予期しないエラーが発生しました"
        )


class KulmsDownloadCli:
    def __init__(self) -> None:
        self.constants = Constants(
            service_name="kulms_download",
            user_name_key="username_key",
            password_key="password_key",
            otp_key="otp_setting_uri_key",
            metadata_fetch_page_size=50,
            concurrent_download=10,
            download_timeout=60.0,
            chunk_bite_size=65536,
            user_data_dir_name="kulms-download",
            default_cookie_exp_delta=timedelta(hours=1)
        )
        self.settings = Settings(self.constants)
        
        self.credential_manager = CredentialManager(self.constants)
        self.password_app_opener = PasswordAppOpener(self.settings)
        self.remote_cookie_fetcher = RemoteCookieFetcher(self.credential_manager, self.password_app_opener, self.constants)
        self.local_cookie_fetcher = LocalCookieManager(self.constants)
        self.cookie_fetcher = CookieFetcher(self.remote_cookie_fetcher, self.local_cookie_fetcher, self.constants)
        
        self.api_client = ApiClient(self.cookie_fetcher, self.constants)
        
        self.metadata_fetcher = MetadataFetcher(self.api_client, self.constants)
        self.resource_downloader = ResourceDownloader(self.api_client, self.constants)
        
        self.console = Console()
    
    async def main(self):
        choices = [
            Choice("サイトリソースのダウンロード", self.download_cli),
            Choice("設定", self.settings_cli)
        ]
        cli_func = await questionary.select("=== KULMS Download ===", choices=choices).unsafe_ask_async()
        await cli_func()

    def _user_message_for_error(self, error: KulmsDownloadError) -> str:
        if isinstance(error, AuthError):
            return f"認証に失敗しました: {error}"
        if isinstance(error, NetworkError):
            return f"ネットワークエラーが発生しました: {error}"
        if isinstance(error, FileSystemError):
            return f"ファイル操作に失敗しました: {error}"
        if isinstance(error, SettingError):
            return f"設定エラーが発生しました: {error}"
        if isinstance(error, ResourceError):
            return f"リソース処理に失敗しました: {error}"
        if isinstance(error, PasswordAppError):
            return f"パスワードアプリの起動に失敗しました: {error}"
        if isinstance(error, CredentialError):
            return f"ECS-IDのパスワードの操作に失敗しました: {error}"
        return str(error) if str(error) else "処理に失敗しました"
    
    async def download_cli(self):
        async with self.api_client as client:
            with self.console.status("サイト情報を取得中..."):
                client.get_cookie()
                site_list = await self.metadata_fetcher.fetch_site_list()
            
            selected_site_list = await questionary.checkbox(
                "資料をダウンロードしたいサイトをすべて選択:",
                choices=list(map(lambda s: Choice(s.title, s), site_list))
            ).unsafe_ask_async()
            
            dest_dir_validate = lambda path_str: True if Path(path_str).is_dir() else "存在するディレクトリを指定してください"
            dest_dir = Path(
                await questionary.path(
                "ダウンロード先のディレクトリパスを入力:",
                default=platformdirs.user_downloads_dir(),
                validate=dest_dir_validate
                ).unsafe_ask_async()
            )
            if not dest_dir.exists():
                raise Exception
            
            confirmation = await questionary.confirm("ダウンロードを開始しますか？").unsafe_ask_async()
            if not confirmation:
                print("中止します。")
                return
            
            with self.console.status("ダウンロード中..."):
                await self.resource_downloader.download_resources_for_site_list(selected_site_list, dest_dir)
            print("ダウンロードが完了しました")
    
    async def settings_cli(self):
        choices = [
            Choice("Cookieの削除", self.delete_cookie_cli),
            Choice("自動入力するECS-IDとパスワードの保存/削除", self.password_setting_cli),
            Choice("認証画面でパスワード管理アプリを自動で開く", self.open_app_setting_cli),
            Choice("ワンタイムパスワードの設定/削除", self.one_time_password_setting_cli)
        ]
        
        next_func = await questionary.select("=== 設定 ===", choices=choices).unsafe_ask_async()
        await next_func()

    async def delete_cookie_cli(self):
        print("Cookieデータはログイン後、1時間程度保持されています。削除すると、次回使用時にログインウインドウが立ち上がります。")
        confirmation = await questionary.confirm("Cookieデータを削除しますか？").unsafe_ask_async()
        if not confirmation:
            print("中止しました。")
            return
        self.local_cookie_fetcher.remove()
        print("Cookieデータを削除しました。")


    async def password_setting_cli(self):
        num = await questionary.select(
            "=== 自動入力するECS-IDとパスワードの保存/削除 ===", 
            choices=[
                Choice("更新,追加", 0),
                Choice("削除", 1)
            ]
        ).unsafe_ask_async()
        
        if num == 0:
            username = await questionary.password("ESC-IDのユーザー名を入力:").unsafe_ask_async()
            password = await questionary.password("ESC-IDのパスワードを入力:").unsafe_ask_async()
            self.credential_manager.set(username, password)
            print("パスワードの設定が完了しました。")
        elif num == 1:
            self.credential_manager.delete()
            print("パスワードを削除しました。") 
    
    async def one_time_password_setting_cli(self):
        num = await questionary.select(
            "=== ワンタイムパスワードの設定 ===", 
            choices=[
                Choice("設定/更新", 0),
                Choice("削除", 1)
            ]
        ).unsafe_ask_async()
        
        if num == 0:
            uri = await questionary.password("ワンタイムパスワードの設定URIを入力 (例: otpauth://totp/......)").unsafe_ask_async()
            self.credential_manager.set_otp_setting_uri(uri)
            print("ワンタイムパスワードの設定が完了しました。")
        elif num == 1:
            self.credential_manager.delete_otp()
            print("ワンタイムパスワードの設定を削除しました。")       

    async def open_app_setting_cli(self):
        print("KULMSのログインウインドウが起動した時に、設定することで同時にパスワード管理アプリを起動させることができます。ワンタイムパスワードの入力がスムーズにできて便利です。")
        
        num = await questionary.select(
            "",
            choices=[
                Choice("パスワード管理アプリの登録", 0),
                Choice("パスワード管理アプリを起動しないようにする", 1)
            ]
        ).unsafe_ask_async()
        
        if num == 0:
            validate = lambda path_str: True if Path(path_str).exists() else "指定されたパスにアプリケーションが存在しません。"
            path_str = await questionary.path(
                "アプリケーションのパスを入力:",
                default=platformdirs.site_applications_dir(),
                validate=validate
            ).unsafe_ask_async()
            self.settings.password_app_path = Path(path_str)
            print("アプリケーションの設定が完了しました。")
        elif num == 1:
            self.settings.password_app_path = None
            print("パスワード管理アプリを起動しないようにしました。")
