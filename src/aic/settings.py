from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    environment: str = Field(default="local", validation_alias="AIC_ENV")
    openai_api_key: str | None = Field(
        default=None, validation_alias="AIC_OPENAI_API_KEY"
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
