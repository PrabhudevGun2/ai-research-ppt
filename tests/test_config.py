"""Tests for configuration and settings."""
import pytest
from backend.config import settings, Settings


class TestSettings:
    def test_settings_loaded(self):
        assert settings.openrouter_api_key, "API key must be set"
        assert settings.openrouter_base_url.startswith("http")
        assert settings.llm_model, "LLM model must be set"

    def test_model_is_fast(self):
        """Verify we're using a fast model for testing."""
        fast_models = [
            "gemini-2.0-flash", "gemini-flash", "gpt-4o-mini",
            "llama-3.1-8b", "haiku", "flash",
        ]
        assert any(m in settings.llm_model.lower() for m in fast_models), (
            f"Expected a fast model for testing, got: {settings.llm_model}"
        )

    def test_output_dir(self):
        assert settings.output_dir

    def test_redis_url(self):
        assert settings.redis_url.startswith("redis://")

    def test_arxiv_max_results(self):
        assert settings.arxiv_max_results > 0
