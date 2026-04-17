from kulms_download.constants import *
import pickle
import platformdirs
import httpx
from datetime import datetime
from pathlib import Path

def __cookie_file_path() -> Path:
    user_data_dir_path = platformdirs.user_data_path(USER_DATA_DIR_NAME)
    user_data_dir_path.mkdir(parents=True, exist_ok=True)
    return user_data_dir_path / "cookie_jar.pickle"

def save_cookies_and_expiration_dt_to_file(cookies: list[CookieInfo], expiration_dt: datetime):
    data_to_save = (cookies, expiration_dt)
    with open(__cookie_file_path(), "wb") as f:
        pickle.dump(data_to_save, f)

def load_cookies_and_expiration_dt_from_file() -> tuple[list[CookieInfo], datetime]|None:
    cookie_file_path = __cookie_file_path()
    if not cookie_file_path.exists():
        return None
    with open(__cookie_file_path(), "rb") as f:
        return pickle.load(f)

def remove_cookies_file():
    __cookie_file_path().unlink(missing_ok=True)