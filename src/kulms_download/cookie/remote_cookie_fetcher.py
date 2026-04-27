from __future__ import annotations

import json
import multiprocessing
import queue
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import cast

import webview

from ..cookie.cookie_jar import CookieJar
from ..cookie.credential_manager import AbstractCredentialManager
from ..cookie.password_app_opener import AbstractPasswordAppOpener
from ..shared.constants import Constants
from ..shared.exceptions import AuthError, CredentialError


class AbstractRemoteCookieFetcher(ABC):
    @abstractmethod
    def fetch(self) -> CookieJar:
        pass


class RemoteCookieFetcher(AbstractRemoteCookieFetcher):
    def __init__(
        self,
        credential_manager: AbstractCredentialManager,
        password_app_opener: AbstractPasswordAppOpener,
        constants: Constants,
    ) -> None:
        self.credential_manager = credential_manager
        self.password_app_opener = password_app_opener
        self.constants = constants

    def fetch(self) -> CookieJar:
        try:
            self.password_app_opener.open()

            cookie_queue = multiprocessing.Queue()
            p = multiprocessing.Process(
                target=self._on_another_process, args=[cookie_queue]
            )
            p.start()
            try:
                jar = cast(CookieJar, cookie_queue.get(timeout=300))
            except queue.Empty as e:
                raise AuthError(
                    "ログインが完了しなかったためCookieを取得できませんでした"
                ) from e
            finally:
                if p.is_alive():
                    p.terminate()
                p.join()

            if not isinstance(jar, CookieJar):
                raise AuthError("サブプロセスからのCookieデータが壊れています")
            return jar
        except AuthError:
            raise
        except Exception as e:
            raise AuthError("Cookie取得中に認証エラーが発生しました") from e

    # この関数が別プロセスで実行される。引数としてはpickle可能なものだけしか許されない。queueはそれに当てはまっている。
    def _on_another_process(self, queue: multiprocessing.Queue):
        core = _RemoteCookieFetcherCore(self.credential_manager, queue, self.constants)
        core.start()


# KULMSのログインウインドウの管理をする主体。
class _RemoteCookieFetcherCore:
    PORTAL_ENTRY_URL = "https://lms.gakusei.kyoto-u.ac.jp/portal"

    def __init__(
        self,
        credential_manager: AbstractCredentialManager,
        queue: multiprocessing.Queue,
        constants: Constants,
    ) -> None:
        self.credential_manager = credential_manager
        self.queue = queue
        self.constants = constants

        w = webview.create_window(
            "Please login to KULMS", url=self.PORTAL_ENTRY_URL, height=800
        )
        if w is None:
            raise AuthError("ログインウィンドウの生成に失敗しました")

        self.window = w
        self.window.events.loaded += self._on_load

    def start(self):
        webview.start()

    def _on_load(self):
        is_logged_in = self.window.evaluate_js(
            "window.portal ? window.portal.loggedIn : false"
        )
        if is_logged_in:
            self._send_queue_to_main_process()
            return

        in_entry_point = self.window.evaluate_js(
            "document.querySelector('#loginLink1') !== null;"
        )
        if in_entry_point:
            self._push_upper_right_login_button()
            return

        there_is_username_field = self.window.evaluate_js(
            "document.querySelector('#username_input') !== null;"
        )
        there_is_onetime_password_field = self.window.evaluate_js(
            "document.querySelector('#password_input.onetime_input') !== null;"
        )
        if there_is_username_field and (there_is_onetime_password_field == False):
            self._fill_double_fields_and_forward()
            return

    def _send_queue_to_main_process(self):
        self.queue.put(CookieJar.from_sc_list(self.window.get_cookies()))

    def _push_upper_right_login_button(self):
        self.window.evaluate_js("document.querySelector('#loginLink1')?.click();")

    def _fill_double_fields_and_forward(self):
        try:
            secret = self.credential_manager.get()
        except CredentialError as e:
            print(
                f"ECS-IDの保存済みパスワードをロードする際にエラーが起きたので、自動入力しません: {e}"
            )
            return

        # パスワードが設定されていない場合はメソッドを抜ける
        if secret is None:
            return
        (username, password) = secret
        self.window.evaluate_js(
            "const el = document.querySelector('#username_input'); if (el) { el.value = %s; }"
            % json.dumps(username)
        )
        self.window.evaluate_js(
            "const el = document.querySelector('#password_input'); if (el) { el.value = %s; }"
            % json.dumps(password)
        )
        self.window.evaluate_js("document.querySelector('#login_button')?.click();")
        time.sleep(0.5)

        self.window.evaluate_js(
            "document.querySelector('#authentication_button')?.click();"
        )
        time.sleep(0.5)
        self.window.evaluate_js("document.querySelector('#choice_button')?.click();")
        time.sleep(0.5)

        otp = self.credential_manager.get_otp(datetime.now())
        if otp is not None:
            self.window.evaluate_js(
                "const el = document.querySelector('#password_input.onetime_input'); if (el) { el.value = %s; }"
                % json.dumps(otp)
            )
            time.sleep(0.5)
            self.window.evaluate_js("document.querySelector('#login_button')?.click();")
            time.sleep(0.5)
