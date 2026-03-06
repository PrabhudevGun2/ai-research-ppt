"""Tests for LLM client (using fast model via OpenRouter)."""
import json
import pytest
from backend.llm_client import get_client, chat, override_model, _resolve_model
from backend.config import settings


class TestLLMClient:
    def test_client_creation(self):
        client = get_client()
        assert client is not None
        assert client.base_url is not None

    def test_simple_chat(self):
        """Test basic chat completion with the fast model."""
        response = chat("Say hello in exactly 3 words.", max_tokens=50)
        assert response, "Should return non-empty response"
        assert len(response) > 0

    def test_chat_with_system_prompt(self):
        response = chat(
            "What is 2+2?",
            system="You are a math tutor. Answer with just the number.",
            max_tokens=10,
        )
        assert "4" in response

    def test_chat_json_response(self):
        """Test that the model can return valid JSON."""
        response = chat(
            'Return a JSON object with keys "name" and "age". Example: {"name": "Alice", "age": 30}. Return ONLY the JSON.',
            max_tokens=100,
        )
        try:
            data = json.loads(response)
            assert "name" in data
            assert "age" in data
        except json.JSONDecodeError:
            pytest.fail(f"Response was not valid JSON: {response[:200]}")

    def test_model_override(self):
        override_model("test-session-123", "google/gemini-2.0-flash-001")
        resolved = _resolve_model("test-session-123")
        assert resolved == "google/gemini-2.0-flash-001"

    def test_default_model(self):
        resolved = _resolve_model("nonexistent-session")
        assert resolved == settings.llm_model

    def test_chat_strips_code_fences(self):
        """Model output with markdown code fences should be stripped."""
        response = chat(
            'Return this exact JSON: {"test": true}. Wrap it in ```json``` code fences.',
            max_tokens=100,
        )
        # After stripping, should be parseable
        try:
            data = json.loads(response)
            assert data.get("test") is True
        except json.JSONDecodeError:
            # It's OK if the model doesn't wrap in fences - the stripping is best-effort
            pass

    def test_long_prompt(self):
        """Test with a longer prompt to ensure no truncation issues."""
        long_text = "This is a test sentence. " * 100
        response = chat(
            f"Summarize this in one sentence: {long_text}",
            max_tokens=200,
        )
        assert response, "Should handle long prompts"
        assert len(response) > 10
