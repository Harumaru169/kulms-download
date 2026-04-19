from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json

from ..shared.constants import Constants
import keyring

class AbstractCredentialManager(ABC):
    @abstractmethod
    def set(self, username, password):
        pass
    
    @abstractmethod
    def get(self) -> tuple[str, str] | None:
        pass
    
    @abstractmethod
    def delete(self):
        pass

class CredentialManager(AbstractCredentialManager):
    def __init__(self, constants: Constants) -> None:
        self.constants = constants
    
    def set(self, username, password):
        keyring.set_password(self.constants.service_name, self.constants.user_name_key, username)
        keyring.set_password(self.constants.service_name, self.constants.password_key, password)
    
    def get(self) -> tuple[str, str] | None:
        username = keyring.get_password(self.constants.service_name, self.constants.user_name_key)
        password = keyring.get_password(self.constants.service_name, self.constants.password_key)

        if username is None or password is None:
            print("🚨 account data is not set!!")
            return None
        else:
            return (username, password)

    def delete(self):
        try:
            keyring.delete_password(self.constants.service_name, self.constants.user_name_key)
            keyring.delete_password(self.constants.service_name, self.constants.password_key)
        except Exception as e:
            print(f"🚨 Failed to delete secrets: {e}")