from __future__ import annotations
from dataclasses import dataclass
from typing import Self, cast
from datetime import datetime, timezone

from http.cookies import SimpleCookie, Morsel
import email.utils
import httpx

@dataclass
class CookieJar:
    pieces: list[_CookiePiece]
    
    @classmethod
    def from_sc_list(cls, sc_list: list[SimpleCookie]) -> Self:
        pieces = []
        for sc in sc_list:
            pieces.extend(_CookiePiece.from_sc(sc))
        return cls(pieces)
    
    def to_httpx_cookies(self):
        jar = httpx.Cookies()
        for piece in self.pieces:
            jar.set(piece.key, piece.value, domain=piece.domain, path=piece.path)
        return jar
    
    def compute_exp_date(self) -> datetime|None:
        result: datetime|None = None
    
        for piece in self.pieces:
            if piece.exp_date is not None:
                if result is None or piece.exp_date < result:
                    result = piece.exp_date
        return result


@dataclass
class _CookiePiece:
    key: str
    value: str
    domain: str
    path: str
    exp_date: datetime|None # expiration datetime
    
    @classmethod
    def from_sc(cls, sc: SimpleCookie) -> list[_CookiePiece]:
        if not sc:
            return []
        return [
            _CookiePiece(
                key=name,
                value=morsel.value,
                domain=morsel["domain"],
                path=morsel["path"],
                exp_date=cls._extract_expiration_date(morsel)
            ) for name, morsel in sc.items()
        ]
    
    # プラットフォームごとにmorselの値の型が変わるのでその差を吸収
    @classmethod
    def _extract_expiration_date(cls, morsel: Morsel) -> datetime | None:
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
