"""Unit tests for LLM providers."""

import pytest
from unittest.mock import patch
from src.llm.gemini import GeminiProvider
from src.llm.openai import OpenAIProvider
from src.llm.ollama import OllamaProvider
from src.llm.provider import AIProvider


def test_gemini_provider_availability():
    # If no key, should not be available
    provider = GeminiProvider(api_key="")
    assert provider.is_available() is False
    
    # If key present, should be available
    provider_with_key = GeminiProvider(api_key="mock_key")
    assert provider_with_key.is_available() is True


def test_openai_provider_availability():
    provider = OpenAIProvider(api_key="")
    assert provider.is_available() is False
    
    provider_with_key = OpenAIProvider(api_key="mock_key")
    assert provider_with_key.is_available() is True


@patch("src.llm.ollama.OllamaProvider.is_available", return_value=True)
@patch("src.llm.ollama.OllamaProvider.list_models", return_value=["qwen2.5-coder:latest"])
def test_ollama_provider(mock_list, mock_avail):
    provider = OllamaProvider()
    assert provider.is_available() is True
    assert "qwen2.5-coder:latest" in provider.list_models()


def test_ai_provider_instantiation():
    provider = AIProvider()
    assert provider is not None

