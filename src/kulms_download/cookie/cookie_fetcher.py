# shared
from __future__ import annotations
from dataclasses import dataclass
from typing import Self, cast
from abc import ABC, abstractmethod
import json
from datetime import datetime, timezone

import httpx
from ..shared.constants import Constants
from ..cookie.cookie_jar import CookieJar
from ..cookie.remote_cookie_fetcher import AbstractRemoteCookieFetcher
from ..cookie.local_cookie_manager import AbstractLocalCookieManager

class AbstractCookieFetcher(ABC):
    @abstractmethod
    def fetch(self) -> CookieJar:
        pass

class CookieFetcher(AbstractCookieFetcher):
    def __init__(
            self,
            remote_cookie_fetcher: AbstractRemoteCookieFetcher,
            local_cookie_manager: AbstractLocalCookieManager,
            constants: Constants
        ) -> None:
        self.remote_cookie_fetcher = remote_cookie_fetcher
        self.local_cookie_manager = local_cookie_manager
        self.constants = constants
    
        # クッキーの保存、有効期限による破棄の判断などもやる
    def fetch(self) -> CookieJar:
        try:
            saved = self.local_cookie_manager.load()
        except Exception as e:
            print(f"保存済みのCookieデータの読み込みにエラーが発生したので、もう一度ログインしてください")
                
        if (saved is None) or (saved[1] < datetime.now(timezone.utc)):
            # 新鮮なクッキーを仕入れる。それをファイルに保存して、returnする。
            jar = self.remote_cookie_fetcher.fetch()
            exp_date = jar.compute_exp_date() or datetime.now() + self.constants.default_cookie_exp_delta
            self.local_cookie_manager.save((jar, exp_date))
        else:
            jar: CookieJar = saved[0]
        
        return jar
