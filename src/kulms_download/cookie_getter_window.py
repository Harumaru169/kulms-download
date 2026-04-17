import multiprocessing
import webview
import time
import json
from kulms_download.constants import *
from kulms_download.secrets_get_set import get_secrets
from kulms_download.cookie_coding import *
from datetime import datetime
import http
from kulms_download.utility import open_app_from_path

PORTAL_ENTRY_URL = "https://lms.gakusei.kyoto-u.ac.jp/portal"

class WindowWorker:
    def __init__(self, queue: multiprocessing.Queue) -> None:
        self.queue = queue
        
        w = webview.create_window(
            "Please login to KULMS",
            url=PORTAL_ENTRY_URL,
            height=800
        )
        if w is None:
            raise Exception
        
        self.window = w
        self.window.events.loaded += self.on_load
        webview.start()

    def on_load(self):
        is_logged_in = self.window.evaluate_js("window.portal ? window.portal.loggedIn : false")
        if is_logged_in:
            self.send_queue_to_main_process()
            return
        
        in_entry_point = self.window.evaluate_js("document.querySelector('#loginLink1') !== null;")
        if in_entry_point:
            self.push_upper_right_login_button()
            return
        
        there_is_username_field = self.window.evaluate_js("document.querySelector('#username_input') !== null;")
        there_is_onetime_password_field = self.window.evaluate_js("document.querySelector('#password_input.onetime_input') !== null;")
        if there_is_username_field and (there_is_onetime_password_field == False):
            self.fill_double_fields_and_forward()
            return
            
    def send_queue_to_main_process(self):
        cookies = cookies_to_list(self.window.get_cookies())
        self.queue.put(cookies)
    
    def push_upper_right_login_button(self):
        self.window.evaluate_js("document.querySelector('#loginLink1')?.click();")
    
    def fill_double_fields_and_forward(self):
        secret = get_secrets()
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

def start_window_worker(queue: multiprocessing.Queue):
    worker = WindowWorker(queue)

def employ_window_worker_and_get_cookie_jar() -> tuple[list[CookieInfo], datetime|None]:
    open_app_from_path()
    
    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=start_window_worker, args=(queue,))
    p.start()
    cookies = queue.get() # list[CookieInfo]
    p.terminate()
    p.join()
    return cookies, compute_earliest_expiration_date(cookies)

if __name__ == '__main__':
    cookie_jar = employ_window_worker_and_get_cookie_jar()
    print("\n正常にGUIを閉じ、CLI側に制御が戻りました！")
    print("取得したCookie:")
    print(cookie_jar)