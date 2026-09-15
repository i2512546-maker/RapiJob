from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL: str = "mysql+mysqlconnector://root:password@localhost:3306/plataforma_servicios_tecnicos"
    
    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Aplicación
    DEBUG: bool = True
    APP_NAME: str = "RapiJob Beta"
    VERSION: str = "0.1.0"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    """Obtener configuración en caché"""
    return Settings()
