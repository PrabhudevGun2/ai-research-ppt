"""
Paper discovery agent - searches ArXiv for papers matching user query.
"""
import logging
import re
from typing import List, Dict, Any

from backend.graph.state import ResearchState, Stage, DiscoveredPaper
from backend.tools.arxiv_tools import search_arxiv, get_paper_details

logger = logging.getLogger(__name__)


def extract_arxiv_id_from_url(url: str) -> str:
    """Extract arxiv ID from various URL formats."""
    # Handle formats like:
    # https://arxiv.org/abs/2401.12345
    # https://arxiv.org/pdf/2401.12345
    # arxiv.org/abs/2401.12345
    # 2401.12345

    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)',
        r'(\d{4}\.\d{4,5})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def paper_discovery_node(state: ResearchState) -> dict:
    """
    Search ArXiv for papers matching the user's query.
    Returns a list of papers for user to select ONE.
    """
    session_id = state["session_id"]
    user_query = state["user_query"]
    arxiv_url = state.get("arxiv_url")
    is_single_paper_mode = state.get("is_single_paper_mode", False)

    logger.info(f"[{session_id}] Paper discovery - query: {user_query}, arxiv_url: {arxiv_url}")

    discovered_papers: List[DiscoveredPaper] = []

    if is_single_paper_mode and arxiv_url:
        # Direct URL mode - extract paper ID and fetch details
        arxiv_id = extract_arxiv_id_from_url(arxiv_url)

        if arxiv_id:
            logger.info(f"[{session_id}] Direct arxiv ID: {arxiv_id}")
            paper = get_paper_details(arxiv_id)

            if paper:
                discovered_papers.append({
                    "arxiv_id": paper["arxiv_id"],
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "summary": paper["summary"],
                    "published": paper["published"],
                    "url": paper["url"],
                    "pdf_url": paper["pdf_url"],
                    "categories": paper["categories"],
                })
            else:
                logger.error(f"[{session_id}] Failed to fetch paper: {arxiv_id}")
                return {
                    "current_stage": Stage.FAILED,
                    "errors": [f"Could not fetch paper from arxiv: {arxiv_id}"],
                }
        else:
            logger.error(f"[{session_id}] Invalid arxiv URL: {arxiv_url}")
            return {
                "current_stage": Stage.FAILED,
                "errors": [f"Invalid arxiv URL format: {arxiv_url}"],
            }
    else:
        # Search mode - find papers matching query
        logger.info(f"[{session_id}] Searching arxiv for: {user_query}")
        papers = search_arxiv(user_query, max_results=20)

        for p in papers:
            discovered_papers.append({
                "arxiv_id": p["arxiv_id"],
                "title": p["title"],
                "authors": p["authors"],
                "summary": p["summary"],
                "published": p["published"],
                "url": p["url"],
                "pdf_url": p["pdf_url"],
                "categories": p["categories"],
            })

    logger.info(f"[{session_id}] Discovered {len(discovered_papers)} papers")

    # If single paper mode with direct URL, skip selection and go to processing
    if is_single_paper_mode and len(discovered_papers) == 1:
        return {
            "current_stage": Stage.PROCESSING_PAPER,
            "discovered_papers": discovered_papers,
            "selected_paper": discovered_papers[0],
        }

    return {
        "current_stage": Stage.AWAITING_PAPER_SELECTION,
        "discovered_papers": discovered_papers,
    }
