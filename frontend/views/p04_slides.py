"""
Slide review page - user reviews and edits 15+ slides before PPT generation.
"""
import streamlit as st
from datetime import datetime
from utils.api_client import resume_session
from utils.session_state import get_session, set_session


SLIDE_TYPE_ICONS = {
    "title": "🎯",
    "problem": "⚠️",
    "background": "📚",
    "contribution": "💡",
    "methodology": "⚙️",
    "architecture": "🏗️",
    "equation": "📐",
    "equations": "📐",
    "algorithm": "🔄",
    "experiments": "🧪",
    "results": "📊",
    "analysis": "🔍",
    "discussion": "💬",
    "limitations": "⛔",
    "future": "🔮",
    "conclusion": "✅",
    "references": "📄",
}


def render():
    st.title("Review Slides")
    st.markdown(
        "Review the **15+ slides** generated from your paper. "
        "Each slide covers a key aspect of the research. Edit as needed."
    )

    payload = get_session("interrupt_payload") or {}
    slides = payload.get("slide_contents", [])
    paper = payload.get("processed_paper", {})

    if not slides:
        st.warning("No slide content available.")
        return

    # Show paper info
    if paper:
        st.info(f"📄 **{paper.get('title', 'Paper')[:80]}...**")

    # Show slide overview metrics
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Slides", len(slides))
    col2.metric("Figures", len(paper.get("figures", [])))
    col3.metric("Tables", len(paper.get("tables", [])))
    col4.metric("Equations", len(paper.get("equations", [])))

    st.divider()

    # Initialize edited slides
    if "edited_slides" not in st.session_state or len(st.session_state.edited_slides) != len(slides):
        st.session_state.edited_slides = [dict(s) for s in slides]

    edited = st.session_state.edited_slides

    # Slide tabs
    st.subheader("Edit Slides")

    for i, slide in enumerate(edited):
        icon = SLIDE_TYPE_ICONS.get(slide.get("slide_type", ""), "📊")
        slide_type = slide.get("slide_type", "content")
        has_image = slide.get("image_path")

        with st.expander(
            f"{icon} Slide {slide['order']}: {slide['title']}{' 🖼️' if has_image else ''}",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                new_title = st.text_input(
                    "Title",
                    value=slide["title"],
                    key=f"slide_title_{i}",
                )
                edited[i]["title"] = new_title

                points_text = "\n".join(slide.get("body_points", []))
                new_points_text = st.text_area(
                    "Bullet Points (one per line)",
                    value=points_text,
                    height=180,
                    key=f"slide_pts_{i}",
                )
                edited[i]["body_points"] = [
                    p.strip() for p in new_points_text.split("\n") if p.strip()
                ]

            with col2:
                st.markdown(f"**Type:** `{slide_type}`")

                if slide.get("image_caption"):
                    st.markdown(f"**Image:** {slide['image_caption'][:50]}...")

                if slide.get("speaker_notes"):
                    with st.expander("Speaker Notes"):
                        st.caption(slide["speaker_notes"][:300])

    st.divider()

    # Compact preview
    st.subheader("Slide Preview")
    preview_cols = st.columns(5)
    for i, slide in enumerate(edited):
        icon = SLIDE_TYPE_ICONS.get(slide.get("slide_type", ""), "📊")
        has_image = "🖼️" if slide.get("image_path") else ""
        preview_cols[i % 5].markdown(
            f"{icon} **{i+1}.** {slide['title'][:25]}...{has_image}"
        )

    st.divider()

    # Feedback and submit
    feedback_text = st.text_area(
        "Feedback (optional)",
        placeholder="e.g. Add more details on methodology...",
        height=60,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Generate PPT", type="primary", use_container_width=True):
            with st.spinner("Creating PowerPoint with images..."):
                try:
                    resume_session(
                        get_session("session_id"),
                        {
                            "action": "approve",
                            "feedback_text": feedback_text or None,
                            "approved_slides": edited,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                    set_session("stage", "generating_ppt")
                    set_session("interrupt_payload", None)
                    st.success(f"Generating {len(edited)} slides...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    with col2:
        st.caption(f"📊 {len(edited)} slides | 🖼️ Images and tables will be included automatically")
