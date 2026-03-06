"""
Paper processor agent - downloads PDF, extracts text, figures, and tables.
"""
import json
import logging
import os
from typing import List, Dict, Any

from backend.graph.state import ResearchState, Stage, ProcessedPaper, ExtractedImage
from backend.tools.pdf_tools import (
    download_arxiv_pdf,
    extract_figures_from_pdf,
    extract_tables_from_pdf,
    extract_equation_regions,
)
from backend.tools.pdf_parser import extract_paper_content
from backend.llm_client import chat
from backend.config import settings

logger = logging.getLogger(__name__)


def paper_processor_node(state: ResearchState) -> dict:
    """
    Process a single paper:
    1. Download PDF
    2. Extract full text
    3. Extract figures, tables, equations via OCR
    4. Return structured paper content
    """
    session_id = state["session_id"]

    # Get selected paper
    selected_paper = state.get("selected_paper")
    if not selected_paper and state.get("discovered_papers"):
        # Auto-select first paper if none selected
        selected_paper = state["discovered_papers"][0]

    if not selected_paper:
        logger.error(f"[{session_id}] No paper to process")
        return {
            "current_stage": Stage.FAILED,
            "errors": ["No paper selected for processing"],
        }

    arxiv_id = selected_paper["arxiv_id"]
    paper_title = selected_paper["title"]
    logger.info(f"[{session_id}] Processing paper: {arxiv_id} - {paper_title}")

    # Create output directory for this session
    output_dir = os.path.join(settings.output_dir, session_id, "assets")
    os.makedirs(output_dir, exist_ok=True)

    # Download PDF
    pdf_path = download_arxiv_pdf(arxiv_id, output_dir=os.path.dirname(output_dir))
    if not pdf_path:
        logger.error(f"[{session_id}] Failed to download PDF for {arxiv_id}")
        return {
            "current_stage": Stage.FAILED,
            "errors": [f"Failed to download PDF for {arxiv_id}"],
        }

    # Extract text content from PDF
    logger.info(f"[{session_id}] Extracting text from PDF...")
    try:
        paper_content = extract_paper_content(pdf_path)
        full_text = paper_content.get("full_text", "")
        sections = paper_content.get("sections", {})
    except Exception as e:
        logger.error(f"[{session_id}] Failed to extract text: {e}")
        full_text = selected_paper.get("summary", "")
        sections = {}

    # Extract figures from PDF
    logger.info(f"[{session_id}] Extracting figures...")
    try:
        figures = extract_figures_from_pdf(pdf_path, output_dir, min_size=150)
        figures_data = [
            {
                "figure_type": f.figure_type,
                "page_num": f.page_num,
                "image_path": f.image_path,
                "caption": f.caption,
                "text_content": f.text_content,
            }
            for f in figures
        ]
    except Exception as e:
        logger.warning(f"[{session_id}] Figure extraction failed: {e}")
        figures_data = []

    # Extract tables from PDF
    logger.info(f"[{session_id}] Extracting tables...")
    try:
        tables = extract_tables_from_pdf(pdf_path, output_dir)
        tables_data = [
            {
                "figure_type": t.figure_type,
                "page_num": t.page_num,
                "image_path": t.image_path,
                "caption": t.caption,
                "text_content": t.text_content,
            }
            for t in tables
        ]
    except Exception as e:
        logger.warning(f"[{session_id}] Table extraction failed: {e}")
        tables_data = []

    # Extract equations from PDF
    logger.info(f"[{session_id}] Extracting equations...")
    try:
        equations = extract_equation_regions(pdf_path, output_dir)
        equations_data = [
            {
                "figure_type": e.figure_type,
                "page_num": e.page_num,
                "image_path": e.image_path,
                "caption": e.caption,
                "text_content": e.text_content,
            }
            for e in equations[:10]  # Limit to top 10 equations
        ]
    except Exception as e:
        logger.warning(f"[{session_id}] Equation extraction failed: {e}")
        equations_data = []

    # Create processed paper object
    processed_paper: ProcessedPaper = {
        "arxiv_id": arxiv_id,
        "title": selected_paper["title"],
        "authors": selected_paper["authors"],
        "abstract": selected_paper["summary"],
        "full_text": full_text[:50000],  # Limit text size
        "sections": sections,
        "figures": figures_data,
        "tables": tables_data,
        "equations": equations_data,
    }

    logger.info(f"[{session_id}] Paper processed: {len(figures_data)} figures, {len(tables_data)} tables, {len(equations_data)} equations")

    return {
        "current_stage": Stage.SYNTHESIZING,
        "processed_paper": processed_paper,
        "selected_paper": selected_paper,
    }
