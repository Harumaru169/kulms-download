# conversion between SimpleCookie and dict
from kulms_download.constants import *
from http.cookies import SimpleCookie, Morsel
from datetime import datetime, timezone
import email.utils
import httpx

# プラットフォームごとにmorselの値の型が変わるのでその差を吸収
def extract_expiration_date(morsel: Morsel) -> datetime | None:
    expires_val = morsel["expires"]

    # expiresが設定されていない場合（空文字列など）
    if not expires_val:
        return None

    # 1. macOS/iOS のブリッジ環境 (NSDate) の場合
    # クラス名ではなくメソッドの有無で判定（ダックタイピング）
    if hasattr(expires_val, "timeIntervalSince1970"):
        timestamp = expires_val.timeIntervalSince1970()
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    # 2. 一般的な Linux / Windows の環境 (str) の場合
    if isinstance(expires_val, str):
        try:
            # 標準的なHTTPのCookie日時（RFC 1123形式）をパース
            return email.utils.parsedate_to_datetime(expires_val)
        except (TypeError, ValueError):
            # 例外的にISOフォーマットで入っていた場合のフォールバック
            try:
                return datetime.fromisoformat(expires_val)
            except ValueError:
                # パース不能な謎の文字列
                return None
                
    return None

def _cookie_to_tuples(sc: SimpleCookie) -> list[CookieInfo]:
    if not sc:
        return []
    return [(name, morsel.value, morsel["domain"], morsel["path"], extract_expiration_date(morsel)) for name, morsel in sc.items()]

def cookies_to_list(scs: list[SimpleCookie]) -> list[CookieInfo]:
    result = []
    for sc in scs:
        result.extend(_cookie_to_tuples(sc))
    return result

def compute_earliest_expiration_date(list: list[CookieInfo]) -> datetime|None:
    result: datetime|None = None
    
    for element in list:
        date = element[4]
        if date is not None:
            if result is None or date < result:
                result = date
    return result

def cookies_to_jar(list: list[CookieInfo]) -> httpx.Cookies:
    jar = httpx.Cookies()
    for (key, value, domain ,path, date) in list:
        jar.set(key,value, domain=domain, path=path)
    return jar

# def list_to_cookie_jar_and_expiration(list: list[tuple[str, str, str, str, datetime|None]]) -> tuple[httpx.Cookies, datetime|None]:
#     jar = httpx.Cookies()
#     earliest_expiration_date: datetime|None = None
#     for (key, value, domain ,path, date) in list:
#         jar.set(key,value, domain=domain, path=path)
        
#         if date is not None:
#             if earliest_expiration_date is None or date < earliest_expiration_date:
#                 earliest_expiration_date = date
    
#     return jar, earliest_expiration_date