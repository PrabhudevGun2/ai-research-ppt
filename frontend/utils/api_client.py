import os
import requests
from typing import Optional

def _build_backend_url() -> str:
    """Build backend URL from env vars. Supports BACKEND_URL directly or host+port parts."""
    url = os.environ.get("BACKEND_URL")
    if url:
        return url.rstrip("/")
    host = os.environ.get("BACKEND_INTERNAL_HOST")
    port = os.environ.get("BACKEND_INTERNAL_PORT")
    if host and port:
        return f"http://{host}:{port}"
    return "http://localhost:8000"

BACKEND_URL = _build_backend_url()
API_BASE = f"{BACKEND_URL}/api/v1"
TIMEOUT = 30


def create_session(user_query: Optional[str] = None, arxiv_url: Optional[str] = None,
                   model: Optional[str] = None, api_key: Optional[str] = None) -> dict:
    """Create a new research session.

    Either user_query OR arxiv_url must be provided.
    api_key is the user's BYOK OpenRouter key (sent securely, never persisted).
    """
    payload = {}
    if arxiv_url:
        payload["arxiv_url"] = arxiv_url
    elif user_query:
        payload["user_query"] = user_query
    else:
        raise ValueError("Either user_query or arxiv_url must be provided")

    if model:
        payload["model"] = model
    if api_key:
        payload["api_key"] = api_key

    resp = requests.post(f"{API_BASE}/sessions", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_session_status(session_id: str) -> dict:
    """Get the current status of a session."""
    resp = requests.get(f"{API_BASE}/sessions/{session_id}/status", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def resume_session(session_id: str, payload: dict) -> dict:
    """Resume a paused session with human feedback."""
    resp = requests.post(
        f"{API_BASE}/sessions/{session_id}/resume", json=payload, timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()


def download_ppt(session_id: str) -> bytes:
    """Download the generated .pptx file as bytes."""
    resp = requests.get(f"{API_BASE}/sessions/{session_id}/ppt/download", timeout=60)
    resp.raise_for_status()
    return resp.content


def download_doc(session_id: str) -> bytes:
    """Download the generated .docx file as bytes."""
    resp = requests.get(f"{API_BASE}/sessions/{session_id}/doc/download", timeout=60)
    resp.raise_for_status()
    return resp.content


def health_check() -> bool:
    """Check if the backend is reachable."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
