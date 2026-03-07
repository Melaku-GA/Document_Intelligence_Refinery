from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Field(..., ...) means this is REQUIRED
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    database_url: str = Field("sqlite:///.refinery/refinery.db", validation_alias="DATABASE_URL")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    # This tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global settings instance
settings = Settings()