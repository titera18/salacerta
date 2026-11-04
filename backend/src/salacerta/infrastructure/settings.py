from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SALACERTA_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./salacerta.db"
