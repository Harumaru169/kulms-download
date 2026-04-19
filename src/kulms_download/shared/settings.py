from __future__ import annotations
from typing import cast
from abc import ABC, abstractmethod
from ..shared.constants import *
from ..shared.exceptions import SettingError
import platformdirs, json
from pathlib import Path

class AbstractSettings(ABC):
    @property
    @abstractmethod
    def password_app_path(self) -> Path|None:
        pass

    @password_app_path.setter
    @abstractmethod
    def password_app_path(self, value: Path|None):
        pass
    

class Settings(AbstractSettings):
    _PERSISTED_FIELDS = ("_password_app_path",)
    
    def __init__(self, constants: Constants) -> None:
        self.constants = constants
        self._password_app_path: str | None = None
    
    def _settings_file_path(self) -> Path:
        user_data_dir_path = platformdirs.user_data_path(self.constants.user_data_dir_name)
        user_data_dir_path.mkdir(parents=True, exist_ok=True)
        return user_data_dir_path / "settings.json"
    
    def _load(self):
        if not self._settings_file_path().exists():
            return

        try:
            with self._settings_file_path().open("r", encoding="utf-8") as f:
                data = json.load(f)
                for field_name in self._PERSISTED_FIELDS:
                    if field_name in data:
                        # self.__dict__ を直接書き換えるか、object.__setattr__ を使う
                        object.__setattr__(self, field_name, data[field_name])
        except Exception as e:
            raise SettingError("設定ファイルの読み込みに失敗しました") from e
    
    def _save(self):
        data = {field_name: getattr(self, field_name) for field_name in self._PERSISTED_FIELDS}
        try:
            with self._settings_file_path().open("w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            raise SettingError("設定ファイルの保存に失敗しました") from e
    
    @property
    def password_app_path(self) -> Path|None:
        self._load()
        if self._password_app_path is None:
            return None
        if not isinstance(self._password_app_path, str):
            raise SettingError(f"設定値 password_app_path が不正です: {self._password_app_path}")
        return Path(cast(str, self._password_app_path))
            
    
    @password_app_path.setter
    def password_app_path(self, value: Path|None):
        if value is None:
            self._password_app_path = value
        else:
            self._password_app_path = str(value)
        self._save()