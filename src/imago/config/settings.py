from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "imago"
    env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    storage_backend: str = "filesystem"
    storage_root: str = "./.data/imago"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="IMAGO_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
