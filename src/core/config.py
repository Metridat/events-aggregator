from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    events_provider_url: str
    events_provider_api_key: str

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
