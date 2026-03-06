import streamlit as st
from utils.api_client import create_session
from utils.session_state import set_session, get_session, STAGE_LABELS

# Curated topic suggestions users can click to pre-fill the query
TOPIC_SUGGESTIONS = [
    "Latest generative AI trends 2025",
    "Large language model advances",
    "Diffusion models and image generation",
    "AI agents and autonomous systems",
    "Multimodal learning: vision + language",
    "Reinforcement learning from human feedback",
    "AI safety and alignment research",
    "Graph neural networks",
    "Retrieval-augmented generation (RAG)",
    "AI in drug discovery and healthcare",
    "Efficient transformers and model compression",
    "Embodied AI and robotics",
]

# Popular OpenRouter model slugs (display name -> model ID)
OPENROUTER_MODELS = {
    "Gemini 2.0 Flash (Google) -- fast & cheap": "google/gemini-2.0-flash-001",
    "Claude Sonnet 4.5 (Anthropic)": "anthropic/claude-sonnet-4-5",
    "Claude 3 Haiku (Anthropic) -- fast & cheap": "anthropic/claude-3-haiku",
    "GPT-4o (OpenAI)": "openai/gpt-4o",
    "GPT-4o Mini (OpenAI) -- fast & cheap": "openai/gpt-4o-mini",
    "Gemini Pro 1.5 (Google)": "google/gemini-pro-1.5",
    "Llama 3.1 70B Instruct (Meta) -- free tier": "meta-llama/llama-3.1-70b-instruct",
    "DeepSeek Chat V3 (DeepSeek)": "deepseek/deepseek-chat",
}


def render():
    st.title("AI Research PPT Generator")
    st.markdown(
        "Generate a professional PowerPoint presentation from a research paper. "
        "Enter an **ArXiv link** to process a specific paper, or **search by topic** to find one."
    )

    # Initialize state
    if "query_text" not in st.session_state:
        st.session_state.query_text = ""
    if "arxiv_url" not in st.session_state:
        st.session_state.arxiv_url = ""

    # -- API Key Input (BYOK) ---------------------------------------------------
    st.subheader("1. Your OpenRouter API Key")
    st.markdown(
        "Your key is used **only for this session** and is **never stored on the server**. "
        "Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys)."
    )

    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-...",
        help="Your key stays in your browser and is sent securely per-request. Never logged or saved to disk.",
        key="user_api_key",
    )

    if api_key:
        st.success("Key provided (hidden for security)")
    else:
        st.info("Please enter your OpenRouter API key to get started.")

    st.divider()

    # -- Option 1: Direct ArXiv URL (PRIORITY) ----------------------------------
    st.subheader("2. Enter ArXiv Paper Link (Recommended)")
    st.markdown("Paste a direct ArXiv URL to create a comprehensive presentation from that paper:")

    arxiv_url = st.text_input(
        "ArXiv URL",
        value=st.session_state.arxiv_url,
        placeholder="e.g., https://arxiv.org/abs/2401.12345 or just 2401.12345",
        help="Paste any ArXiv abstract or PDF URL. The paper will be processed automatically.",
        key="arxiv_url_input",
    )

    if arxiv_url and ("arxiv.org" in arxiv_url or len(arxiv_url.split("/")[-1].replace(".", "")) >= 8):
        st.success("Valid ArXiv link detected - will process this paper directly")

    st.divider()

    # -- Option 2: Topic Search -------------------------------------------------
    st.subheader("3. Or Search by Topic")
    st.markdown("Search ArXiv for papers on a topic, then select one to present:")

    st.markdown("**Quick picks** -- click to search:")
    cols = st.columns(3)
    for i, suggestion in enumerate(TOPIC_SUGGESTIONS):
        with cols[i % 3]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.query_text = suggestion
                st.session_state.arxiv_url = ""

    user_query = st.text_input(
        "Or type your search query",
        value=st.session_state.query_text,
        placeholder="e.g. multimodal foundation models for robotics",
        help="Search ArXiv for papers matching your query, then select one.",
        key="query_text_input",
    )

    # -- Model selector ---------------------------------------------------------
    st.subheader("4. Choose Model")
    model_display = st.selectbox(
        "LLM model (via OpenRouter)",
        options=list(OPENROUTER_MODELS.keys()),
        index=0,
        help="Any model on OpenRouter can be used. Cost and speed vary.",
    )
    selected_model_id = OPENROUTER_MODELS[model_display]
    st.caption(f"Model ID: `{selected_model_id}`")

    # -- Launch -----------------------------------------------------------------
    st.subheader("5. Start")
    col1, col2 = st.columns([1, 3])
    with col1:
        start_clicked = st.button("Start", type="primary", use_container_width=True)

    if start_clicked:
        if not api_key:
            st.error("Please enter your OpenRouter API key above.")
            return

        # Priority: arxiv URL over query
        if arxiv_url and ("arxiv.org" in arxiv_url or len(arxiv_url.replace(".", "").replace("/", "")) >= 8):
            with st.spinner("Starting paper processing..."):
                try:
                    result = create_session(
                        arxiv_url=arxiv_url.strip(),
                        model=selected_model_id,
                        api_key=api_key,
                    )
                    set_session("session_id", result["session_id"])
                    set_session("arxiv_url", arxiv_url.strip())
                    set_session("stage", result["status"])
                    st.success("Session started! Processing paper...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start session: {e}")
        elif user_query.strip():
            with st.spinner("Searching ArXiv..."):
                try:
                    result = create_session(
                        user_query=user_query.strip(),
                        model=selected_model_id,
                        api_key=api_key,
                    )
                    set_session("session_id", result["session_id"])
                    set_session("user_query", user_query.strip())
                    set_session("stage", result["status"])
                    st.success(f"Session started! Found papers for: {user_query[:50]}...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to start session: {e}")
        else:
            st.warning("Please enter an ArXiv URL or a search query.")

    # -- How it works ------------------------------------------------------------
    with st.expander("How it works", expanded=False):
        st.markdown("""
**Pipeline Steps:**
1. **Input Paper** -- Provide an ArXiv link or search for papers by topic
2. **Paper Selection** -- If searching, select ONE paper from results
3. **Paper Processing** -- Download PDF, extract text, figures, and tables
4. **Slide Creation** -- Generate 15+ comprehensive slides from the paper
5. **Slide Review** -- Review and edit slide content
6. **PPT Generation** -- Create professional PowerPoint with images
7. **Download** -- Get your .pptx file

**Security:**
- Your API key is stored only in your browser session
- It is sent to our backend per-request and used transiently
- The key is never logged, saved to disk, or shared with anyone
- All communication uses HTTPS in production
        """)


def render_progress():
    """Show a progress screen while the pipeline is running."""
    stage = get_session("stage")
    label = STAGE_LABELS.get(stage, "Processing...")
    st.title("AI Research PPT Generator")

    if stage == "processing_paper":
        st.info("**Processing Paper** -- Extracting text, figures, and tables from PDF...")
    elif stage == "synthesizing":
        st.info("**Creating Slides** -- Generating comprehensive presentation content...")
    elif stage == "generating_ppt":
        st.info("**Building PPT** -- Creating PowerPoint with images...")
    else:
        st.info(f"**{label}** -- Please wait...")

    with st.spinner(label):
        pass
    st.caption("This page will automatically advance when ready.")
