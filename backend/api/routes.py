import asyncio
import glob
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.graph.builder import build_graph, get_checkpointer
from backend.graph.state import Stage
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session tracking (stage + interrupt payload)
_session_registry: dict[str, dict] = {}

MAX_SESSIONS = 5  # Keep at most this many sessions in memory


class CreateSessionRequest(BaseModel):
    user_query: Optional[str] = None
    arxiv_url: Optional[str] = None  # Direct arxiv link (takes precedence)
    model: Optional[str] = None   # override LLM_MODEL env var for this session
    api_key: Optional[str] = None  # BYOK: user's OpenRouter API key (never logged/persisted)


class ResumeRequest(BaseModel):
    action: str = "approve"
    feedback_text: Optional[str] = None
    selected_paper: Optional[dict] = None  # For paper selection
    approved_slides: Optional[list] = None
    timestamp: Optional[str] = None


def _get_thread_config(session_id: str) -> dict:
    return {"configurable": {"thread_id": session_id}}


def _cleanup_old_sessions(keep_session: str = ""):
    """Remove oldest sessions when we exceed MAX_SESSIONS to free memory."""
    if len(_session_registry) <= MAX_SESSIONS:
        return

    # Sort by stage - completed/failed sessions are safe to remove first
    removable = []
    for sid, reg in _session_registry.items():
        if sid == keep_session:
            continue
        stage = reg.get("stage", "")
        if stage in (Stage.COMPLETED, Stage.FAILED):
            removable.append(sid)

    # If not enough completed/failed, remove oldest sessions
    if len(_session_registry) - len(removable) > MAX_SESSIONS:
        for sid in list(_session_registry.keys()):
            if sid != keep_session and sid not in removable:
                removable.append(sid)

    for sid in removable:
        _cleanup_session(sid)
        if len(_session_registry) <= MAX_SESSIONS:
            break


def _cleanup_session(session_id: str):
    """Remove a session's data from memory and disk."""
    logger.info(f"Cleaning up session {session_id}")

    # Remove session assets directory (PDFs, extracted images)
    session_dir = os.path.join(settings.output_dir, session_id)
    if os.path.isdir(session_dir):
        shutil.rmtree(session_dir, ignore_errors=True)

    # Remove generated files
    for ext in ("*.pptx", "*.docx"):
        for f in glob.glob(os.path.join(settings.output_dir, f"{session_id}{ext}")):
            try:
                os.remove(f)
            except OSError:
                pass

    # Remove from registry
    _session_registry.pop(session_id, None)

    # Clean up BYOK key
    try:
        from backend.llm_client import cleanup_session
        cleanup_session(session_id)
    except Exception:
        pass


async def _run_graph(session_id: str, initial_state: dict):
    """Run the LangGraph pipeline in the background."""
    try:
        from backend.llm_client import set_current_session
        set_current_session(session_id)
        checkpointer = get_checkpointer()
        graph = build_graph(checkpointer=checkpointer)
        config = _get_thread_config(session_id)

        _session_registry[session_id] = {
            "stage": Stage.DISCOVERING_PAPERS,
            "interrupt_payload": None,
            "error": None,
        }

        # Run until first interrupt or completion
        result = await asyncio.to_thread(
            graph.invoke, initial_state, config
        )
        _update_session_from_state(session_id, result)

    except Exception as e:
        logger.error(f"[{session_id}] Graph error: {e}", exc_info=True)
        _session_registry[session_id]["stage"] = Stage.FAILED
        _session_registry[session_id]["error"] = str(e)


def _update_session_from_state(session_id: str, state: dict):
    """Update in-memory registry from graph state."""
    if not state:
        return
    stage = state.get("current_stage", Stage.COMPLETED)
    registry = _session_registry.setdefault(session_id, {})
    registry["stage"] = stage

    # Only keep what's needed - drop heavy data after PPT is generated
    if stage in (Stage.AWAITING_FINAL_REVIEW, Stage.COMPLETED):
        # Keep only file paths, drop full_text/processed_paper to free memory
        light_state = {
            "generated_ppt": state.get("generated_ppt"),
            "current_stage": stage,
        }
        registry["state"] = light_state
    else:
        registry["state"] = state

    # Capture interrupt payload based on stage
    if stage == Stage.AWAITING_PAPER_SELECTION:
        registry["interrupt_payload"] = {
            "discovered_papers": state.get("discovered_papers", []),
        }
    elif stage == Stage.AWAITING_SYNTHESIS_REVIEW:
        registry["interrupt_payload"] = {
            "slide_contents": state.get("slide_contents", []),
            "processed_paper": state.get("processed_paper"),
        }
    elif stage == Stage.AWAITING_FINAL_REVIEW:
        registry["interrupt_payload"] = {
            "generated_ppt": state.get("generated_ppt"),
            "errors": state.get("errors", []),
        }
    else:
        registry["interrupt_payload"] = None


async def _resume_graph(session_id: str, resume_data: dict):
    """Resume a paused graph with human feedback."""
    try:
        from langgraph.types import Command
        from backend.llm_client import set_current_session
        set_current_session(session_id)
        checkpointer = get_checkpointer()
        graph = build_graph(checkpointer=checkpointer)
        config = _get_thread_config(session_id)

        registry = _session_registry.get(session_id, {})
        registry["stage"] = "resuming"

        result = await asyncio.to_thread(
            graph.invoke,
            Command(resume=resume_data),
            config,
        )
        _update_session_from_state(session_id, result)

    except Exception as e:
        logger.error(f"[{session_id}] Resume error: {e}", exc_info=True)
        _session_registry[session_id]["stage"] = Stage.FAILED
        _session_registry[session_id]["error"] = str(e)


@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    background_tasks: BackgroundTasks,
):
    """Create a new research session and start the pipeline."""
    session_id = str(uuid.uuid4())
    # Clean up old sessions to keep memory usage low
    _cleanup_old_sessions(keep_session=session_id)
    # BYOK: store user's API key for this session (in-memory only)
    if request.api_key:
        from backend.llm_client import set_session_api_key
        set_session_api_key(session_id, request.api_key)
    # Override model for this session if supplied
    if request.model:
        from backend.llm_client import override_model
        override_model(session_id, request.model)

    # Determine mode: direct arxiv URL or topic search
    is_single_paper_mode = bool(request.arxiv_url)
    initial_stage = Stage.DISCOVERING_PAPERS

    initial_state = {
        "session_id": session_id,
        "user_query": request.user_query or "",
        "arxiv_url": request.arxiv_url,
        "is_single_paper_mode": is_single_paper_mode,
        "current_stage": initial_stage,
        "discovered_papers": [],
        "selected_paper": None,
        "processed_paper": None,
        "slide_contents": [],
        "approved_slides": [],
        "generated_ppt": None,
        "human_feedback_history": [],
        "errors": [],
    }

    _session_registry[session_id] = {
        "stage": initial_stage,
        "interrupt_payload": None,
        "error": None,
    }

    background_tasks.add_task(_run_graph, session_id, initial_state)

    if is_single_paper_mode:
        logger.info(f"Created session {session_id} for arxiv URL: {request.arxiv_url}")
    else:
        logger.info(f"Created session {session_id} for query: {request.user_query}")

    return {"session_id": session_id, "status": initial_stage}


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Poll the current stage and any interrupt payload."""
    registry = _session_registry.get(session_id)
    if registry is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "stage": registry.get("stage", Stage.DISCOVERING_PAPERS),
        "interrupt_payload": registry.get("interrupt_payload"),
        "error": registry.get("error"),
    }


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    request: ResumeRequest,
    background_tasks: BackgroundTasks,
):
    """Submit human feedback and resume the graph."""
    registry = _session_registry.get(session_id)
    if registry is None:
        raise HTTPException(status_code=404, detail="Session not found")

    stage = registry.get("stage")
    awaiting_stages = {
        Stage.AWAITING_PAPER_SELECTION,
        Stage.AWAITING_SYNTHESIS_REVIEW,
        Stage.AWAITING_FINAL_REVIEW,
    }
    if stage not in awaiting_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Session is not awaiting human input (current stage: {stage})",
        )

    resume_data = {
        "action": request.action,
        "feedback_text": request.feedback_text,
        "timestamp": request.timestamp or datetime.utcnow().isoformat(),
    }
    if request.selected_paper is not None:
        resume_data["selected_paper"] = request.selected_paper
    if request.approved_slides is not None:
        resume_data["approved_slides"] = request.approved_slides

    registry["stage"] = "resuming"
    registry["interrupt_payload"] = None

    background_tasks.add_task(_resume_graph, session_id, resume_data)
    return {"session_id": session_id, "status": "resuming"}


@router.get("/sessions/{session_id}/ppt/download")
async def download_ppt(session_id: str):
    """Stream the generated .pptx file."""
    from backend.config import settings
    import os

    registry = _session_registry.get(session_id)
    if registry is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = registry.get("state", {})
    generated_ppt = state.get("generated_ppt")
    if not generated_ppt:
        raise HTTPException(status_code=404, detail="PPT not yet generated")

    file_path = generated_ppt.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PPT file not found on disk")

    filename = f"ai_research_{session_id[:8]}.pptx"
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@router.get("/sessions/{session_id}/doc/download")
async def download_doc(session_id: str):
    """Stream the generated .docx file."""
    import os

    registry = _session_registry.get(session_id)
    if registry is None:
        raise HTTPException(status_code=404, detail="Session not found")

    state = registry.get("state", {})
    generated_ppt = state.get("generated_ppt")
    if not generated_ppt:
        raise HTTPException(status_code=404, detail="Document not yet generated")

    doc_path = generated_ppt.get("doc_path")
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    filename = f"ai_research_{session_id[:8]}.docx"
    return FileResponse(
        path=doc_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@router.get("/health")
async def health_check():
    """Liveness probe."""
    return {"status": "healthy", "service": "ai-research-ppt-backend"}
