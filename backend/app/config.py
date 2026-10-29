import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres@localhost:5432/datapilot",
        description="Primary database connection string"
    )
    TEST_DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres@localhost:5432/datapilot_test",
        description="Test database connection string"
    )

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ]

    ARTIFACTS_DIR: str = "artifacts"
    DATA_DIR: str = "data"

    DEFAULT_OBSERVATION_DAYS: int = 90
    DEFAULT_PREDICTION_DAYS: int = 60
    RANDOM_SEED: int = 42


settings = Settings()
