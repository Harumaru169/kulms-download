from __future__ import annotations
from typing import cast
from abc import ABC, abstractmethod
import json

import multiprocessing, webview
from ..shared.constants import Constants
from ..cookie.cookie_jar import CookieJar
from ..cookie.credential_manager import AbstractCredentialManager
from ..cookie.password_app_opener import AbstractPasswordAppOpener

class AbstractRemoteCookieFetcher(ABC):
    @abstractmethod
    def fetch(self) -> CookieJar:
        pass

class RemoteCookieFetcher(AbstractRemoteCookieFetcher):
    def __init__(
            self,
            credential_manager: AbstractCredentialManager,
            password_app_opener: AbstractPasswordAppOpener,
            constants: Constants) -> None:
        self.credential_manager = credential_manager
        self.password_app_opener = password_app_opener
        self.constants = constants

    def fetch(self) -> CookieJar:
        self.password_app_opener.open()
        
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=self._on_another_process, args=[queue])
        p.start()
        jar = cast(CookieJar, queue.get())
        p.terminate()
        p.join()
        return jar
    
    # この関数が別プロセスで実行される。引数としてはpickle可能なものだけしか許されない。queueはそれに当てはまっている。
    def _on_another_process(self, queue: multiprocessing.Queue):
        core = _RemoteCookieFetcherCore(self.credential_manager, queue, self.constants)
        core.start()


# KULMSのログインウインドウの管理をする主体。
class _RemoteCookieFetcherCore:
    PORTAL_ENTRY_URL = "https://lms.gakusei.kyoto-u.ac.jp/portal"
    
    def __init__(self, credential_manager: AbstractCredentialManager, queue: multiprocessing.Queue, constants: Constants) -> None:
        self.credential_manager = credential_manager
        self.queue = queue
        self.constants = constants
        
        w = webview.create_window(
            "Please login to KULMS",
            url=self.PORTAL_ENTRY_URL,
            height=800
        )
        if w is None:
            raise Exception
        
        self.window = w
        self.window.events.loaded += self._on_load
    
    def start(self):
        webview.start()

    def _on_load(self):
        is_logged_in = self.window.evaluate_js("window.portal ? window.portal.loggedIn : false")
        if is_logged_in:
            self._send_queue_to_main_process()
            return
        
        in_entry_point = self.window.evaluate_js("document.querySelector('#loginLink1') !== null;")
        if in_entry_point:
            self._push_upper_right_login_button()
            return
        
        there_is_username_field = self.window.evaluate_js("document.querySelector('#username_input') !== null;")
        there_is_onetime_password_field = self.window.evaluate_js("document.querySelector('#password_input.onetime_input') !== null;")
        if there_is_username_field and (there_is_onetime_password_field == False):
            self._fill_double_fields_and_forward()
            return
            
    def _send_queue_to_main_process(self):
        self.queue.put(CookieJar.from_sc_list(self.window.get_cookies()))
    
    def _push_upper_right_login_button(self):
        self.window.evaluate_js("document.querySelector('#loginLink1')?.click();")
    
    def _fill_double_fields_and_forward(self):
        secret = self.credential_manager.get()
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
        return
