import time
import streamlit as st

from utils.session_state import init_session, get_session, set_session, STAGE_TO_PAGE, STAGE_LABELS
from utils.api_client import get_session_status, health_check, wake_backend

st.set_page_config(
    page_title="AI Research PPT Generator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session()

# --- Wake backend before rendering anything -----------------------------------
if "backend_ready" not in st.session_state:
    st.session_state.backend_ready = False

if not st.session_state.backend_ready:
    if not health_check(timeout=8):
        st.title("AI Research PPT Generator")
        st.info("Backend is starting up (Render free tier cold start). Please wait...")
        with st.spinner("Waking up backend — this takes up to 60 seconds..."):
            ok = wake_backend()
        if ok:
            st.session_state.backend_ready = True
            st.rerun()
        else:
            st.error("Backend did not respond. Please refresh the page in 30 seconds.")
            st.stop()
    else:
        st.session_state.backend_ready = True

# --- Sidebar ------------------------------------------------------------------
with st.sidebar:
    st.title("AI Research PPT")
    st.caption("Paper to Presentation")
    st.divider()

    session_id = get_session("session_id")
    if session_id:
        st.metric("Session", session_id[:8] + "...")
        stage = get_session("stage")
        label = STAGE_LABELS.get(stage, stage or "—")
        st.metric("Stage", label)
        st.divider()

    st.success("Backend connected")

    if st.button("Start New Session", use_container_width=True):
        from utils.session_state import clear_session
        clear_session()
        st.rerun()

st.divider()

# Polling: if we have an active session that is in a processing stage, poll
PROCESSING_STAGES = {
    "discovering_papers", "processing_paper", "synthesizing",
    "generating_ppt", "resuming",
}

if session_id and get_session("stage") in PROCESSING_STAGES:
    try:
        status = get_session_status(session_id)
        new_stage = status.get("stage")
        set_session("stage", new_stage)
        set_session("interrupt_payload", status.get("interrupt_payload"))
        set_session("error", status.get("error"))
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.error(f"Polling error: {e}")

# Page routing
page = STAGE_TO_PAGE.get(get_session("stage") or "", "start")

if page == "start" and not get_session("session_id"):
    from views import p01_start
    p01_start.render()
elif page == "start":
    # Still processing
    from views import p01_start
    p01_start.render_progress()
elif page == "papers":
    from views import p02_topics
    p02_topics.render()
elif page in ("synthesis_progress", "generating_progress"):
    stage_label = STAGE_LABELS.get(get_session("stage"), "Processing...")
    st.info(f"{stage_label} Please wait...")
    with st.spinner(stage_label):
        time.sleep(3)
    st.rerun()
elif page == "slides":
    from views import p04_slides
    p04_slides.render()
elif page == "final":
    from views import p05_final
    p05_final.render()
elif page == "error":
    st.error(f"Pipeline failed: {get_session('error')}")
    if st.button("Restart"):
        from utils.session_state import clear_session
        clear_session()
        st.rerun()
else:
    from views import p01_start
    p01_start.render()
