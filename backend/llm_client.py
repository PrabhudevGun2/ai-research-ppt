"""
Shared OpenRouter LLM client.

OpenRouter exposes an OpenAI-compatible REST API, so we use the `openai`
SDK pointed at https://openrouter.ai/api/v1.

Supports two modes:
  1. Server-side key: OPENROUTER_API_KEY env var (legacy / admin)
  2. BYOK (Bring Your Own Key): user provides key per-session via frontend.
     The key is held in memory only for the session lifetime, never logged or
     persisted to disk.
"""
import logging
import httpx
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

# Shared client using server-side env key (may be None if BYOK-only)
_default_client: OpenAI | None = None
# session_id -> dedicated OpenAI client (for BYOK sessions)
_session_clients: dict[str, OpenAI] = {}
# session_id -> model slug overrides
_session_models: dict[str, str] = {}
# thread-local session context (set by the background task runner)
_current_session_id: str | None = None


def _build_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=settings.openrouter_base_url,
        timeout=httpx.Timeout(300.0, connect=30.0),
    )


def get_client(session_id: str | None = None) -> OpenAI:
    """Return the OpenAI client for a session.

    Priority:
      1. Per-session BYOK client
      2. Shared server-side client (from env)
    """
    sid = session_id or _current_session_id

    # Check for BYOK client first
    if sid and sid in _session_clients:
        return _session_clients[sid]

    # Fall back to shared server-side client
    global _default_client
    if _default_client is None:
        key = settings.openrouter_api_key
        if not key:
            raise ValueError(
                "No API key available. Please provide your OpenRouter API key."
            )
        _default_client = _build_client(key)
    return _default_client


def set_session_api_key(session_id: str, api_key: str) -> None:
    """Store a BYOK API key for a session. Key is kept in memory only."""
    _session_clients[session_id] = _build_client(api_key)


def cleanup_session(session_id: str) -> None:
    """Remove all session-specific data (key, model override)."""
    _session_clients.pop(session_id, None)
    _session_models.pop(session_id, None)


def override_model(session_id: str, model: str) -> None:
    """Register a model override for a specific session."""
    _session_models[session_id] = model


def set_current_session(session_id: str) -> None:
    """Called by the graph runner to set the active session context."""
    global _current_session_id
    _current_session_id = session_id


def _resolve_model(session_id: str | None = None) -> str:
    sid = session_id or _current_session_id
    return _session_models.get(sid, settings.llm_model) if sid else settings.llm_model


def chat(
    prompt: str,
    max_tokens: int = 2000,
    system: str | None = None,
    session_id: str | None = None,
) -> str:
    """
    Send a single-turn chat prompt via OpenRouter and return the text response.
    Strips markdown code fences automatically.
    """
    client = get_client(session_id)
    model = _resolve_model(session_id)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    logger.info(f"Sending request to {model}, max_tokens={max_tokens}, prompt_len={len(prompt)}")
    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://github.com/ai-research-ppt",
                "X-Title": "AI Research PPT Generator",
            },
        )
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        raise

    logger.info(f"Got response, choices={len(response.choices)}")
    if not response.choices:
        logger.warning("LLM returned empty choices")
        return ""

    content = response.choices[0].message.content
    if content is None:
        logger.warning("LLM returned None content")
        return ""

    raw = content.strip()
    logger.info(f"Response length: {len(raw)} chars")

    # Strip ```json ... ``` or ``` ... ``` fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) >= 2 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()
