from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    APP_NAME: str = "Sample FastAPI"
    APP_VERSION: str = "0.1.0"
    APP_LOG_LEVEL: str = "DEBUG"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8080

settings = Settings()
    