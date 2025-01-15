from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    
    # Database Settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: str
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Odoo Settings
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USERNAME: str
    ODOO_PASSWORD: str
    
    # Redis Settings
    REDIS_HOST: str
    REDIS_PORT: int
    
    # Email Settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    FRONTEND_URL: str

    @property
    def DATABASE_URL(self) -> str:
        """Get full database URL."""
        return self.SQLALCHEMY_DATABASE_URI
    
    @property
    def REDIS_URL(self) -> str:
        """Get full Redis URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()