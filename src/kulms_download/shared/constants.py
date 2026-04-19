from dataclasses import dataclass
from datetime import timedelta

@dataclass
class Constants:
    # keyring
    service_name: str
    user_name_key: str
    password_key: str
    
    # download
    concurrent_download: int
    download_timeout: float
    chunk_bite_size: int
    
    #persistence
    user_data_dir_name: str
    
    # cookie expiration
    default_cookie_exp_delta: timedelta