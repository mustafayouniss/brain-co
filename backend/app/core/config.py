from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/orgbrain_legal"
    )
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "orgbrain_legal"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_TEST_DB: str = "orgbrain_legal_test"

    @property
    def TEST_DATABASE_URL(self) -> str:
        """Connection URL for the isolated test database."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_TEST_DB}"
        )


settings = Settings()
