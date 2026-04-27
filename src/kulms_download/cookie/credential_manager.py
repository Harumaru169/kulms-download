from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import keyring
import keyring.errors
import pyotp

from ..shared.constants import Constants
from ..shared.exceptions import CredentialError


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

    @abstractmethod
    def set_otp_setting_uri(self, uri):
        pass

    @abstractmethod
    def get_otp(self, target_dt: datetime) -> str | None:
        pass

    @abstractmethod
    def delete_otp(self):
        pass


class CredentialManager(AbstractCredentialManager):
    def __init__(self, constants: Constants) -> None:
        self.constants = constants

    def set(self, username, password):
        try:
            keyring.set_password(
                self.constants.service_name, self.constants.user_name_key, username
            )
            keyring.set_password(
                self.constants.service_name, self.constants.password_key, password
            )
        except keyring.errors.KeyringError as e:
            raise CredentialError("ECS-IDのパスワードがセットできませんでした") from e

    def get(self) -> tuple[str, str] | None:
        try:
            username = keyring.get_password(
                self.constants.service_name, self.constants.user_name_key
            )
            password = keyring.get_password(
                self.constants.service_name, self.constants.password_key
            )
        except keyring.errors.KeyringError as e:
            raise CredentialError("ECS-IDのパスワードが取得できませんでした") from e

        if username is None or password is None:
            print("🚨 account data is not set!!")
            return None
        else:
            return (username, password)

    def delete(self):
        try:
            keyring.delete_password(
                self.constants.service_name, self.constants.user_name_key
            )
            keyring.delete_password(
                self.constants.service_name, self.constants.password_key
            )
        except keyring.errors.KeyringError as e:
            raise CredentialError("ECS-IDのパスワードが削除できませんでした") from e

    def set_otp_setting_uri(self, uri):
        try:
            keyring.set_password(
                self.constants.service_name, self.constants.otp_key, uri
            )
        except keyring.errors.KeyringError as e:
            raise CredentialError("OTP設定URIがセットできませんでした") from e

    def get_otp(self, target_dt: datetime) -> str | None:
        try:
            uri = keyring.get_password(
                self.constants.service_name, self.constants.otp_key
            )
        except keyring.errors.KeyringError as e:
            raise CredentialError("OTP設定URIが取得できませんでした") from e
        if uri is None:
            print("🚨 OTP setting URI is not set!!")
            return None
        totp = pyotp.parse_uri(uri)
        otp_code = totp.at(target_dt)
        return otp_code

    def delete_otp(self):
        try:
            keyring.delete_password(self.constants.service_name, self.constants.otp_key)
        except keyring.errors.KeyringError as e:
            raise CredentialError("OTP設定URIが削除できませんでした") from e
