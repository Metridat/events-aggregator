from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str
    postgres_port: int
    postgres_username: str
    postgres_password: str
    postgres_database_name: str
    events_provider_url: str
    events_provider_api_key: str

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_username}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database_name}"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
