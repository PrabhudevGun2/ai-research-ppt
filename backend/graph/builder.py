import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from backend.graph.state import ResearchState, Stage
from backend.agents.paper_discovery import paper_discovery_node
from backend.agents.paper_processor import paper_processor_node
from backend.agents.slide_synthesis import slide_synthesis_node
from backend.agents.ppt_generation import ppt_generation_node
from backend.config import settings

logger = logging.getLogger(__name__)


def human_paper_selection_node(state: ResearchState) -> dict:
    """Interrupt point: human selects ONE paper from discovered papers."""
    logger.info(f"[{state['session_id']}] Waiting for human paper selection")
    feedback = interrupt({
        "stage": Stage.AWAITING_PAPER_SELECTION,
        "discovered_papers": state["discovered_papers"],
        "message": "Please select ONE paper to create a presentation from.",
    })
    return {
        "current_stage": Stage.PROCESSING_PAPER,
        "selected_paper": feedback.get("selected_paper"),
        "human_feedback_history": [{
            "stage": Stage.AWAITING_PAPER_SELECTION,
            "action": feedback.get("action", "approve"),
            "feedback_text": feedback.get("feedback_text"),
            "modified_data": {"selected_paper": feedback.get("selected_paper")},
            "timestamp": feedback.get("timestamp", ""),
        }],
    }


def human_synthesis_review_node(state: ResearchState) -> dict:
    """Interrupt point: human reviews and edits slide content."""
    logger.info(f"[{state['session_id']}] Waiting for human synthesis review")
    feedback = interrupt({
        "stage": Stage.AWAITING_SYNTHESIS_REVIEW,
        "slide_contents": state["slide_contents"],
        "processed_paper": state.get("processed_paper"),
        "message": "Please review and edit the slide content.",
    })
    return {
        "current_stage": Stage.GENERATING_PPT,
        "approved_slides": feedback.get("approved_slides", state["slide_contents"]),
        "human_feedback_history": [{
            "stage": Stage.AWAITING_SYNTHESIS_REVIEW,
            "action": feedback.get("action", "approve"),
            "feedback_text": feedback.get("feedback_text"),
            "modified_data": {"approved_slides": feedback.get("approved_slides")},
            "timestamp": feedback.get("timestamp", ""),
        }],
    }


def human_final_review_node(state: ResearchState) -> dict:
    """Interrupt point: human reviews the final PPT."""
    logger.info(f"[{state['session_id']}] Waiting for final review")
    feedback = interrupt({
        "stage": Stage.AWAITING_FINAL_REVIEW,
        "generated_ppt": state["generated_ppt"],
        "message": "Your presentation is ready. Please review and download.",
    })
    return {
        "current_stage": Stage.COMPLETED,
        "human_feedback_history": [{
            "stage": Stage.AWAITING_FINAL_REVIEW,
            "action": feedback.get("action", "approve"),
            "feedback_text": feedback.get("feedback_text"),
            "modified_data": None,
            "timestamp": feedback.get("timestamp", ""),
        }],
    }


def route_after_discovery(state: ResearchState) -> str:
    """Route after paper discovery: skip human selection in single-paper mode."""
    if state.get("is_single_paper_mode") and state.get("selected_paper"):
        return "process_paper"
    return "human_paper_selection"


def build_graph(checkpointer=None) -> StateGraph:
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(ResearchState)

    # Add all nodes
    graph.add_node("paper_discovery", paper_discovery_node)
    graph.add_node("human_paper_selection", human_paper_selection_node)
    graph.add_node("paper_processor", paper_processor_node)
    graph.add_node("slide_synthesis", slide_synthesis_node)
    graph.add_node("human_synthesis_review", human_synthesis_review_node)
    graph.add_node("ppt_generation", ppt_generation_node)
    graph.add_node("human_final_review", human_final_review_node)

    # Always start with paper discovery
    graph.add_edge(START, "paper_discovery")

    # After discovery: skip human selection if single-paper mode auto-selected
    graph.add_conditional_edges(
        "paper_discovery",
        route_after_discovery,
        {
            "human_paper_selection": "human_paper_selection",
            "process_paper": "paper_processor",
        }
    )

    # Human paper selection -> paper processor
    graph.add_edge("human_paper_selection", "paper_processor")

    # Paper processing -> Synthesis
    graph.add_edge("paper_processor", "slide_synthesis")

    # Synthesis -> Human Review -> PPT Generation
    graph.add_edge("slide_synthesis", "human_synthesis_review")
    graph.add_edge("human_synthesis_review", "ppt_generation")

    # PPT Generation -> Final Review -> End
    graph.add_edge("ppt_generation", "human_final_review")
    graph.add_edge("human_final_review", END)

    return graph.compile(checkpointer=checkpointer)


def get_checkpointer():
    """Create a checkpointer. Uses Redis if RediSearch is available, else in-memory."""
    try:
        from langgraph.checkpoint.redis import RedisSaver
        ctx = RedisSaver.from_conn_string(settings.redis_url)
        saver = ctx.__enter__()
        saver.setup()
        logger.info("Using Redis checkpointer")
        return saver
    except Exception as e:
        logger.warning(f"Redis checkpointer unavailable ({e}), using in-memory checkpointer")
        return MemorySaver()
