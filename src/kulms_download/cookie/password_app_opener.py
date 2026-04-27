from __future__ import annotations

import os
import platform
import subprocess
from abc import ABC, abstractmethod

from ..shared.exceptions import PasswordAppError
from ..shared.settings import AbstractSettings


class AbstractPasswordAppOpener(ABC):
    @abstractmethod
    def open(self):
        pass


class PasswordAppOpener(AbstractPasswordAppOpener):
    def __init__(self, settings: AbstractSettings) -> None:
        self.settings = settings

    def open(self):
        if not self.settings.password_app_path:
            return

        path = self.settings.password_app_path
        if not path.exists():
            raise PasswordAppError(
                f"パスワードアプリが見つかりません: {self.settings.password_app_path}"
            )

        current_os = platform.system()

        if current_os == "Windows":
            os.startfile(path)

        elif current_os == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)

        else:  # Linux (Ubuntu等)
            subprocess.run(["xdg-open", str(path)], check=True)
