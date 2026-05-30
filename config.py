from functools import lru_cache
from pydantic_settings import SettingsConfigDict , BaseSettings 

class Settings(BaseSettings) : 
    
    model_config = SettingsConfigDict(env_file = ".env" , env_file_encoding = "utf-8" , case_sensitive = False)
    MODEL_PATH : str  
    HOST  : str 
    PORT : int  
    WORKERS : int 
    CONNECTION_STR  :str  
    CORS_ORIGINS : list[str] = ["*"] # only for now .
    
@lru_cache
def get_settings() -> Settings : 
    return Settings() 