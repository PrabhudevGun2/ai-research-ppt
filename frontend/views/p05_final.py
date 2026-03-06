import streamlit as st
from datetime import datetime
from utils.api_client import resume_session, download_ppt, download_doc
from utils.session_state import get_session, set_session


def render():
    st.title("Download Presentation")

    payload = get_session("interrupt_payload") or {}
    generated_ppt = payload.get("generated_ppt")
    errors = payload.get("errors", [])
    stage = get_session("stage")

    if stage == "completed" or generated_ppt:
        st.success("Your presentation and document are ready!")

        if generated_ppt:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Slides", generated_ppt.get("slide_count", "---"))
            with col2:
                st.metric("Generated", generated_ppt.get("generated_at", "---"))
            with col3:
                has_doc = bool(generated_ppt.get("doc_path"))
                st.metric("Formats", "PPTX + DOCX" if has_doc else "PPTX")

            topics = generated_ppt.get("topics_covered", [])
            if topics:
                st.markdown(f"**Paper:** {topics[0][:100]}...")

        if errors:
            with st.expander("Notes"):
                for e in errors:
                    st.warning(e)

        st.divider()
        st.subheader("Download Files")
        session_id = get_session("session_id")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**PowerPoint Presentation**")
            st.caption("Professional slides with figures and tables")
            try:
                pptx_bytes = download_ppt(session_id)
                st.download_button(
                    label="Download .pptx",
                    data=pptx_bytes,
                    file_name=f"research_ppt_{session_id[:8]}.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.error(f"PPT download failed: {e}")

        with col2:
            st.markdown("**Word Document**")
            st.caption("Detailed companion doc with full content and speaker notes")
            try:
                docx_bytes = download_doc(session_id)
                st.download_button(
                    label="Download .docx",
                    data=docx_bytes,
                    file_name=f"research_doc_{session_id[:8]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            except Exception:
                st.caption("Word document not available for this session.")

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            if stage != "completed":
                if st.button("Mark Complete", use_container_width=True):
                    with st.spinner("Finalizing..."):
                        try:
                            resume_session(
                                session_id,
                                {
                                    "action": "approve",
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            )
                            set_session("stage", "completed")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")

        with col2:
            if st.button("Start New", use_container_width=True):
                from utils.session_state import clear_session
                clear_session()
                st.rerun()

    else:
        st.info("Waiting for presentation to be generated...")
        st.caption("The page will update automatically.")
