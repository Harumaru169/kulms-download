from __future__ import annotations
from kulms_download.constants import *
import json
import platformdirs
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Any

def _settings_file_path() -> Path:
    user_data_dir_path = platformdirs.user_data_path(USER_DATA_DIR_NAME)
    user_data_dir_path.mkdir(parents=True, exist_ok=True)
    return user_data_dir_path / "settings.json"

@dataclass
class _AbstractSettings:
    # 設定ファイルの保存先。デフォルト引数を持たないフィールドを先に書く必要があるため、
    # 実際の設定項目は子クラスで定義します。
    def __post_init__(self):
        # 初期化完了フラグ。これがないと __init__ 中の代入で毎回保存が走る
        object.__setattr__(self, "_initialized", False)
        
        self._config_path = _settings_file_path()
        self._load()
        
        object.__setattr__(self, "_initialized", True)
    
    # ファイルが存在すれば読み込み、属性に反映する
    def _load(self):
        if not self._config_path.exists():
            return

        try:
            with self._config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                for field in fields(self):
                    if field.name in data:
                        # self.__dict__ を直接書き換えるか、object.__setattr__ を使う
                        object.__setattr__(self, field.name, data[field.name])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load settings: {e}")

    def _save(self):
        """現在の値を JSON に書き出す"""
        with self._config_path.open("w", encoding="utf-8") as f:
            # asdictを使うと、dataclassのフィールドのみを抽出できる
            json.dump(asdict(self), f, indent=4, ensure_ascii=False)

    def __setattr__(self, name: str, value: Any):
        # 通常の代入処理
        super().__setattr__(name, value)
        
        # 初期化が完了しており、かつプライベート変数（_開始）でない属性の変更時に保存
        if getattr(self, "_initialized", False) and not name.startswith("_"):
            self._save()

@dataclass
class Settings(_AbstractSettings):
    password_app_executable_path: str|None = None

shared_settings = Settings()