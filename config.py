from functools import lru_cache
from pydantic_settings import SettingsConfigDict , BaseSettings 

class SharedConfigSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Prevents crashing if extra vars are present in .env
    )


class modelSettings(SharedConfigSettings) : 
    model_config = SettingsConfigDict(env_prefix="MODEL_")
    PATH : str  
    
class appSettings(SharedConfigSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")
    HOST  : str 
    PORT : int  
    WORKERS : int 
    CORS_ORIGINS : list[str] = ["*"] # only for now .

class dataBaseSettings(SharedConfigSettings):
    model_config = SettingsConfigDict(env_prefix="PG_")
    CONNECTION_STR  :str  
    
class Settings(): 
    def __init__(self,):
        self.app   = appSettings()
        self.model = modelSettings()
        self.database = dataBaseSettings()

@lru_cache
def get_settings() -> Settings : 
    return Settings() 