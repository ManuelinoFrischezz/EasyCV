"""Application settings using pydantic-settings.

Settings are loaded from environment variables with the EASYCV_ prefix,
or from a .env file in the project root.

Example .env file:
    EASYCV_LLM_PROVIDER=anthropic
    EASYCV_LLM_MODEL=claude-sonnet-4-20250514
    EASYCV_LLM_TEMPERATURE=0.0
    ANTHROPIC_API_KEY=sk-ant-...
    OPENAI_API_KEY=sk-...
    OPENROUTER_API_KEY=sk-or-...

Usage:
    >>> from easycv.settings import get_settings
    >>> settings = get_settings()
    >>> print(settings.llm.provider)
    'anthropic'
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Settings for LLM provider and model configuration.

    Attributes:
        provider: Which LLM provider to use.
        model: Model identifier (provider-specific naming).
        temperature: Sampling temperature (0.0 = deterministic).
        max_tokens: Maximum tokens in response.
    """

    model_config = SettingsConfigDict(
        env_prefix="EASYCV_LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["openai", "anthropic", "openrouter"] = Field(
        default="openrouter",
        description="LLM provider: openai, anthropic, or openrouter",
    )
    model: str = Field(
        default="anthropic/claude-sonnet-4-20250514",
        description="Model identifier (use provider prefix for OpenRouter)",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic)",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens in response",
    )


class APIKeySettings(BaseSettings):
    """API keys for LLM providers.

    Keys are loaded from environment variables without prefix,
    following the convention of each provider's SDK.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: SecretStr | None = Field(
        default=None,
        description="OpenAI API key",
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        description="Anthropic API key",
    )
    openrouter_api_key: SecretStr | None = Field(
        default=None,
        description="OpenRouter API key",
    )


class Settings(BaseSettings):
    """Root settings container."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    api_keys: APIKeySettings = Field(default_factory=APIKeySettings)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Settings are loaded once and cached for the lifetime of the process.
    To reload settings (e.g., in tests), use `get_settings.cache_clear()`.

    Returns:
        Application settings loaded from environment.
    """
    return Settings()
