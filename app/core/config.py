from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API
    log_level: str = Field(default="info", env="LOG_LEVEL")
    port: int = Field(default=8000, env="PORT")
    default_max_tokens: int = Field(default=512, env="DEFAULT_MAX_TOKENS")

    # LLM (Bedrock): family = claude | llama | titan | ministral
    llm_provider: str = Field(default="bedrock", env="LLM_PROVIDER")
    llm_family: str = Field(default="claude", env="LLM_FAMILY")
    llm_model: str = Field(default="", env="LLM_MODEL")
    llm_max_tokens: int | None = Field(default=None, env="LLM_MAX_TOKENS")
    llm_temperature: float | None = Field(default=None, env="LLM_TEMPERATURE")
    llm_streaming: bool = Field(default=True, env="LLM_STREAMING")

    # AWS Bedrock
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    bedrock_timeout: int = Field(default=120, env="BEDROCK_TIMEOUT")

    # Health
    health_check_timeout_seconds: int = Field(default=300, env="HEALTH_CHECK_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
