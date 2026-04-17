import keyring
from kulms_download.constants import *

def set_secrets(username, password):
    keyring.set_password(SERVICE_NAME, USER_NAME_KEY, username)
    keyring.set_password(SERVICE_NAME, PASSWORD_KEY, password)

def get_secrets() -> tuple[str, str] | None:
    username = keyring.get_password(SERVICE_NAME, USER_NAME_KEY)
    password = keyring.get_password(SERVICE_NAME, PASSWORD_KEY)

    if username is None or password is None:
        print("🚨 account data is not set!!")
        return None
    else:
        return (username, password)

def delete_secrets():
    try:
        keyring.delete_password(SERVICE_NAME, USER_NAME_KEY)
        keyring.delete_password(SERVICE_NAME, PASSWORD_KEY)
    except Exception as e:
        print(f"🚨 Failed to delete secrets: {e}")
