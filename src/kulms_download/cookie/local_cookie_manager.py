from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import platformdirs

from ..cookie.cookie_jar import CookieJar
from ..shared.constants import Constants
from ..shared.exceptions import FileSystemError

type LocalCookieData = tuple[CookieJar, datetime]


class AbstractLocalCookieManager(ABC):
    @abstractmethod
    def save(self, data: LocalCookieData):
        pass

    @abstractmethod
    def load(self) -> LocalCookieData | None:
        pass

    @abstractmethod
    def remove(self):
        pass


# ローカルにCookieJarを保存、また引き出しを担当
class LocalCookieManager(AbstractLocalCookieManager):
    def __init__(self, constants: Constants) -> None:
        self.constants = constants

    def __cookie_file_path(self) -> Path:
        user_data_dir_path = platformdirs.user_data_path(
            self.constants.user_data_dir_name
        )
        user_data_dir_path.mkdir(parents=True, exist_ok=True)
        return user_data_dir_path / "cookie_jar.pickle"

    def save(self, data: LocalCookieData):
        try:
            with open(self.__cookie_file_path(), "wb") as f:
                pickle.dump(data, f)
        except (OSError, pickle.PickleError) as e:
            raise FileSystemError("Cookieデータの保存に失敗しました") from e

    def load(self) -> LocalCookieData | None:
        path = self.__cookie_file_path()
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except (OSError, pickle.UnpicklingError, EOFError, ValueError) as e:
            raise FileSystemError("Cookieデータの読み込みに失敗しました") from e

    def remove(self):
        try:
            self.__cookie_file_path().unlink(missing_ok=True)
        except OSError as e:
            raise FileSystemError("Cookieデータの削除に失敗しました") from e
