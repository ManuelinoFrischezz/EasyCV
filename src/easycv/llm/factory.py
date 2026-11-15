"""LLM factory for creating chat models from different providers.

This module provides a unified interface to create LangChain chat models
for OpenAI, Anthropic, and OpenRouter. The factory reads from settings
to determine which provider and model to use.

Usage:
    >>> from easycv.llm.factory import create_llm
    >>> from easycv.settings import get_settings
    >>>
    >>> llm = create_llm(get_settings())
    >>> response = llm.invoke("Hello!")

OpenRouter uses the OpenAI-compatible API, so we use ChatOpenAI with
a different base_url.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from easycv.settings import APIKeySettings, LLMSettings, Settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class LLMConfigurationError(Exception):
    """Raised when LLM configuration is invalid or incomplete."""


def create_llm(settings: Settings) -> BaseChatModel:
    """Create a LangChain chat model based on settings.

    Args:
        settings: Application settings containing provider, model, and API keys.

    Returns:
        A LangChain BaseChatModel instance configured for the specified provider.

    Raises:
        LLMConfigurationError: If the API key for the selected provider is missing,
            or if an unknown provider is specified.

    Example:
        >>> settings = get_settings()
        >>> llm = create_llm(settings)
        >>> # Use with structured output
        >>> structured_llm = llm.with_structured_output(MySchema)
    """
    llm_settings = settings.llm
    api_keys = settings.api_keys

    match llm_settings.provider:
        case "openai":
            return _create_openai(llm_settings, api_keys)
        case "anthropic":
            return _create_anthropic(llm_settings, api_keys)
        case "openrouter":
            return _create_openrouter(llm_settings, api_keys)
        case _:
            raise LLMConfigurationError(f"Unknown provider: {llm_settings.provider}")


def _create_openai(
    llm_settings: LLMSettings,
    api_keys: APIKeySettings,
) -> ChatOpenAI:
    """Create an OpenAI chat model."""
    if api_keys.openai_api_key is None:
        raise LLMConfigurationError(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
        )

    return ChatOpenAI(
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        max_completion_tokens=llm_settings.max_tokens,
        api_key=api_keys.openai_api_key,
    )


def _create_anthropic(
    llm_settings: LLMSettings,
    api_keys: APIKeySettings,
) -> ChatAnthropic:
    """Create an Anthropic chat model."""
    if api_keys.anthropic_api_key is None:
        raise LLMConfigurationError(
            "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable."
        )

    return ChatAnthropic(
        model=llm_settings.model,  # type: ignore[call-arg]
        max_tokens=llm_settings.max_tokens,
        api_key=SecretStr(api_keys.anthropic_api_key.get_secret_value()),
    )


def _create_openrouter(
    llm_settings: LLMSettings,
    api_keys: APIKeySettings,
) -> ChatOpenAI:
    """Create an OpenRouter chat model.

    OpenRouter uses the OpenAI-compatible API, so we use ChatOpenAI
    with a different base_url.
    """
    if api_keys.openrouter_api_key is None:
        raise LLMConfigurationError(
            "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable."
        )

    return ChatOpenAI(
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        max_completion_tokens=llm_settings.max_tokens,
        api_key=api_keys.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
    )
