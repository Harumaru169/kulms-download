from datetime import datetime, timedelta
type CookieInfo = tuple[str, str, str, str, datetime|None]

# keyring
SERVICE_NAME = "kulms_download"
USER_NAME_KEY = "username_key"
PASSWORD_KEY = "password_key"

# download
CONCURRENT_DOWNLOAD = 10
DOWNLOAD_TIMEOUT = 60.0
CHUNK_BITE_SIZE = 65536

# persistence
USER_DATA_DIR_NAME = "kulms-download"

# cookie expiration
DEFAULT_COOKIE_EXPIRATION = timedelta(hours=1)