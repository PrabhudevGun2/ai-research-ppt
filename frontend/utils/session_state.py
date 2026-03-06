import streamlit as st
from typing import Any, Optional


def init_session():
    """Initialize all required session state keys."""
    defaults = {
        "session_id": None,
        "user_query": "",
        "stage": None,
        "interrupt_payload": None,
        "error": None,
        "polling": False,
        "page": "start",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_session(key: str, value: Any):
    st.session_state[key] = value


def get_session(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)


def clear_session():
    """Reset all session state (start fresh)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session()


STAGE_TO_PAGE = {
    "discovering_papers": "start",
    "processing_paper": "start",
    "resuming": "start",
    "awaiting_paper_selection": "papers",
    "synthesizing": "synthesis_progress",
    "awaiting_synthesis_review": "slides",
    "generating_ppt": "generating_progress",
    "awaiting_final_review": "final",
    "completed": "final",
    "failed": "error",
}

STAGE_LABELS = {
    "discovering_papers": "Searching ArXiv...",
    "processing_paper": "Processing paper...",
    "resuming": "Processing your feedback...",
    "synthesizing": "Creating slides...",
    "generating_ppt": "Generating presentation...",
    "awaiting_paper_selection": "Select a paper",
    "awaiting_synthesis_review": "Review slides",
    "awaiting_final_review": "Ready for download",
    "completed": "Completed",
    "failed": "Failed",
}
