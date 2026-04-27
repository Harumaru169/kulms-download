class KulmsDownloadError(Exception):
    pass


class AuthError(KulmsDownloadError):
    pass


class NetworkError(KulmsDownloadError):
    pass


class FileSystemError(KulmsDownloadError):
    pass


class SettingError(KulmsDownloadError):
    pass


class ResourceError(KulmsDownloadError):
    pass


class PasswordAppError(KulmsDownloadError):
    pass


class CredentialError(KulmsDownloadError):
    pass
