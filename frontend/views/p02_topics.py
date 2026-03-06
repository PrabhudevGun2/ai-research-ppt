"""
Paper selection page - user selects ONE paper from discovered papers.
"""
import streamlit as st
from datetime import datetime
from utils.api_client import resume_session
from utils.session_state import get_session, set_session


def render():
    st.title("Select a Paper")
    st.markdown(
        "**Select ONE paper** to create a comprehensive presentation. "
        "The system will extract text, figures, and tables from the PDF."
    )

    payload = get_session("interrupt_payload") or {}
    discovered = payload.get("discovered_papers", [])

    if not discovered:
        st.warning("No papers found. Please go back and try a different search.")
        if st.button("Start Over"):
            from utils.session_state import clear_session
            clear_session()
            st.rerun()
        return

    st.subheader(f"Found {len(discovered)} Papers")

    # Track selected paper index
    selected_idx = None

    for i, paper in enumerate(discovered):
        with st.container():
            col1, col2 = st.columns([0.08, 0.92])

            with col1:
                # Radio button for selection
                if st.button("Select", key=f"select_{i}", type="primary"):
                    selected_idx = i

            with col2:
                # Paper details
                title = paper.get("title", "Untitled")
                authors = paper.get("authors", [])
                published = paper.get("published", "")
                categories = paper.get("categories", [])
                summary = paper.get("summary", "")
                arxiv_id = paper.get("arxiv_id", "")

                st.markdown(f"**{title}**")

                # Meta info row
                meta_parts = []
                if authors:
                    meta_parts.append(f"👥 {', '.join(authors[:3])}" + (" et al." if len(authors) > 3 else ""))
                if published:
                    meta_parts.append(f"📅 {published}")
                if categories:
                    meta_parts.append(f"🏷️ {categories[0]}")
                if arxiv_id:
                    meta_parts.append(f"[arXiv:{arxiv_id}](https://arxiv.org/abs/{arxiv_id})")

                st.caption(" | ".join(meta_parts))

                # Abstract in expander
                with st.expander("Abstract"):
                    st.markdown(summary[:1000] + ("..." if len(summary) > 1000 else ""))

        st.divider()

    # If a paper was selected, submit and continue
    if selected_idx is not None:
        selected_paper = discovered[selected_idx]

        with st.spinner(f"Processing: {selected_paper['title'][:50]}..."):
            try:
                resume_session(
                    get_session("session_id"),
                    {
                        "action": "approve",
                        "selected_paper": selected_paper,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                set_session("stage", "processing_paper")
                set_session("interrupt_payload", None)
                st.success(f"Selected: {selected_paper['title'][:60]}...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit selection: {e}")

    # Instructions
    st.info("💡 Click **Select** on the paper you want to present. The system will download the PDF and extract content for 15+ slides.")
