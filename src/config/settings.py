from pydantic_settings import BaseSettings


class SentinelSettings(BaseSettings):
    """Project settings loaded from environment variables and .env file."""

    github_token: str = ""
    ai_provider: str = "mock"
    ai_endpoint: str = "https://models.inference.ai.azure.com"
    ai_model: str = "gpt-4o"

    model_config = {"env_prefix": "SENTINEL_", "env_file": ".env", "extra": "ignore"}


def load_settings() -> SentinelSettings:
    return SentinelSettings()
