"""
Slide synthesis agent - creates presentation from processed paper.
Focuses on methodology, results, and visual content (figures/tables).
"""
import json
import logging
import os
from datetime import date

from backend.graph.state import ResearchState, Stage, SlideContent
from backend.llm_client import chat

logger = logging.getLogger(__name__)

# Target number of slides
TARGET_SLIDES = 15


def slide_synthesis_node(state: ResearchState) -> dict:
    """
    Create a presentation focused on methodology, results, and visual content.
    Bullet points are concise (10-20 words). Heavy use of figures/tables.
    """
    session_id = state["session_id"]
    paper = state.get("processed_paper")

    if not paper:
        logger.error(f"[{session_id}] No processed paper available")
        return {
            "current_stage": Stage.FAILED,
            "errors": ["No processed paper available for slide synthesis"],
        }

    logger.info(f"[{session_id}] Synthesizing slides for paper: {paper['title']}")

    # Prepare paper content for LLM
    paper_content = f"""
TITLE: {paper['title']}

AUTHORS: {', '.join(paper['authors'][:5])}

ABSTRACT:
{paper['abstract']}

"""

    # Add sections if available
    for section_name, content in paper.get('sections', {}).items():
        if section_name != 'references':
            paper_content += f"\n\n## {section_name.upper()}\n{content}\n"

    # Add figure/table info
    figures = paper.get('figures', [])
    tables = paper.get('tables', [])
    all_assets = figures + tables

    if figures:
        paper_content += f"\n\n## AVAILABLE FIGURES ({len(figures)})\n"
        for i, fig in enumerate(figures):
            paper_content += f"- Figure {i+1}: {fig.get('caption', 'No caption')}\n"

    if tables:
        paper_content += f"\n\n## AVAILABLE TABLES ({len(tables)})\n"
        for i, tbl in enumerate(tables):
            paper_content += f"- Table {i+1}: {tbl.get('caption', 'No caption')}\n"

    n_figures = len(figures)
    n_tables = len(tables)

    prompt = f"""You are an expert AI researcher creating a CONCISE, VISUAL slide deck.

PAPER CONTENT:
{paper_content}

CRITICAL RULES - READ CAREFULLY:
1. Keep bullet points SHORT: 10-20 words max per bullet. No walls of text.
2. Use 3-5 bullet points per slide, not more.
3. FOCUS on methodology and results - these should get 60%+ of slides.
4. Every figure and table from the paper MUST appear on a slide.
5. Speaker notes carry the detailed explanation (100-200 words).
6. Avoid generic filler - be specific with numbers, names, metrics.

AVAILABLE VISUALS: {n_figures} figures, {n_tables} tables.
You MUST use ALL of them. Assign each to a slide via "recommended_figure".

SLIDE STRUCTURE (exactly {TARGET_SLIDES} slides):

1. **Title** - Paper title, authors, date, arxiv link (1 slide)
2. **Problem & Motivation** - What problem, why it matters (1 slide)
3. **Key Contributions** - 3-5 main contributions as short bullets (1 slide)
4. **Methodology** - 3-5 slides covering the approach, architecture, key techniques. USE FIGURES HERE.
5. **Results & Comparisons** - 3-5 slides with quantitative results. USE TABLES HERE. Include exact numbers.
6. **Analysis / Ablation** - What works, what doesn't (1-2 slides)
7. **Limitations & Future Work** - Honest assessment + next steps (1 slide)
8. **Conclusion** - Key takeaways (1 slide)

FOR EACH SLIDE, return JSON:
{{
  "slide_type": "title|problem|contribution|methodology|architecture|results|analysis|limitations|future|conclusion",
  "title": "Specific slide title",
  "subtitle": "Section context",
  "body_points": [
    "Short point 1 (10-20 words with specific details)",
    "Short point 2 with numbers or method names",
    "Short point 3"
  ],
  "speaker_notes": "100-200 words of presenter prose with full context and transitions.",
  "order": integer,
  "recommended_figure": "Figure X" or "Table Y" or null
}}

BULLET POINT EXAMPLES (good vs bad):
- GOOD: "Transformer achieves 28.4 BLEU on EN-DE, +2.0 over previous SOTA"
- BAD: "The proposed transformer-based architecture demonstrates significant improvements in machine translation quality as measured by BLEU scores when compared against the previous state-of-the-art methods"
- GOOD: "LangGraph: 94% task completion via explicit state management"
- BAD: "The LangGraph framework achieved a task completion rate of 94% which can be attributed to its explicit state management approach that provides structured workflows"

IMAGE ASSIGNMENT RULES:
- You have {n_figures} figures and {n_tables} tables available
- EVERY figure/table MUST be assigned to exactly one slide
- Methodology/architecture slides -> assign figures (architecture diagrams)
- Results/comparison slides -> assign tables (comparison data)
- If a slide has a figure/table, keep text minimal (2-3 short bullets)

Today's date: {date.today().strftime("%B %d, %Y")}
ArXiv ID: {paper['arxiv_id']}

Return ONLY a valid JSON array of {TARGET_SLIDES} slides."""

    try:
        raw = chat(prompt, max_tokens=12000)
        logger.info(f"[{session_id}] LLM returned {len(raw)} chars, parsing JSON...")
        slides_data = json.loads(raw)
        logger.info(f"[{session_id}] Parsed {len(slides_data)} slides from JSON")
    except json.JSONDecodeError as e:
        logger.error(f"[{session_id}] JSON parse failed: {e}, raw[:200]={raw[:200]}")
        slides_data = _fallback_slides(paper)
    except Exception as e:
        logger.error(f"[{session_id}] LLM synthesis failed: {e}")
        slides_data = _fallback_slides(paper)

    # Process slides and match with figures/tables
    slides: list[SlideContent] = []
    used_figures = set()
    used_tables = set()

    for i, s in enumerate(slides_data):
        slide = {
            "slide_type": s.get("slide_type", "content"),
            "topic": paper['title'][:50],
            "title": s.get("title", f"Slide {i+1}"),
            "subtitle": s.get("subtitle"),
            "body_points": s.get("body_points", []),
            "speaker_notes": s.get("speaker_notes"),
            "order": s.get("order", i + 1),
            "image_path": None,
            "image_caption": None,
        }

        # Match recommended figure/table
        rec = s.get("recommended_figure") or ""
        if rec:
            slide["image_path"], slide["image_caption"] = _find_matching_asset(
                rec, figures, tables
            )
            if slide["image_path"]:
                # Track which assets are used
                import re
                m = re.match(r'(Figure|Table)\s*(\d+)', rec, re.I)
                if m:
                    if m.group(1).lower() == "figure":
                        used_figures.add(int(m.group(2)) - 1)
                    else:
                        used_tables.add(int(m.group(2)) - 1)

        slides.append(slide)

    # Ensure ALL unused figures/tables get assigned to slides
    _assign_unused_assets(slides, figures, tables, used_figures, used_tables)

    slides.sort(key=lambda x: x["order"])
    logger.info(f"[{session_id}] Generated {len(slides)} slides")

    return {
        "current_stage": Stage.AWAITING_SYNTHESIS_REVIEW,
        "slide_contents": slides,
    }


def _assign_unused_assets(slides, figures, tables, used_figures, used_tables):
    """Ensure every figure and table appears on at least one slide."""
    # Find unused figures
    for idx, fig in enumerate(figures):
        if idx not in used_figures and fig.get("image_path"):
            # Find best slide to attach to (methodology/architecture preferred)
            best = _find_best_slide_for_asset(slides, "figure", fig)
            if best:
                if not best.get("image_path"):
                    best["image_path"] = fig.get("image_path")
                    best["image_caption"] = fig.get("caption")
                else:
                    # Add as new slide
                    _insert_asset_slide(slides, fig, "figure")

    # Find unused tables
    for idx, tbl in enumerate(tables):
        if idx not in used_tables and tbl.get("image_path"):
            best = _find_best_slide_for_asset(slides, "table", tbl)
            if best:
                if not best.get("image_path"):
                    best["image_path"] = tbl.get("image_path")
                    best["image_caption"] = tbl.get("caption")
                else:
                    _insert_asset_slide(slides, tbl, "table")


def _find_best_slide_for_asset(slides, asset_type, asset):
    """Find the best existing slide to attach an asset to."""
    # For figures: prefer methodology/architecture slides without images
    # For tables: prefer results/analysis slides without images
    if asset_type == "figure":
        preferred = {"methodology", "architecture", "method", "contribution"}
    else:
        preferred = {"results", "analysis", "experiments", "evaluation"}

    # First pass: preferred type without image
    for s in slides:
        if s.get("slide_type") in preferred and not s.get("image_path"):
            return s
    # Second pass: any slide without image (skip title/conclusion)
    for s in slides:
        if s.get("slide_type") not in {"title", "conclusion"} and not s.get("image_path"):
            return s
    return None


def _insert_asset_slide(slides, asset, asset_type):
    """Insert a new slide dedicated to showing an asset."""
    caption = asset.get("caption", "")
    max_order = max((s.get("order", 0) for s in slides), default=0)
    slide_type = "results" if asset_type == "table" else "methodology"
    slides.append({
        "slide_type": slide_type,
        "topic": caption[:50] if caption else asset_type.title(),
        "title": caption[:80] if caption else f"{asset_type.title()} from Paper",
        "subtitle": None,
        "body_points": [caption] if caption else [],
        "speaker_notes": f"This slide shows {caption or 'a visual from the paper'}.",
        "order": max_order + 1,
        "image_path": asset.get("image_path"),
        "image_caption": caption,
    })


def _find_matching_asset(recommendation: str, figures: list, tables: list) -> tuple:
    """Find matching figure or table from recommendation."""
    import re

    match = re.match(r'(Figure|Table)\s*(\d+)', recommendation, re.I)
    if not match:
        return None, None

    asset_type = match.group(1).lower()
    asset_num = int(match.group(2))

    if asset_type == "figure" and asset_num <= len(figures):
        fig = figures[asset_num - 1]
        return fig.get("image_path"), fig.get("caption")
    elif asset_type == "table" and asset_num <= len(tables):
        tbl = tables[asset_num - 1]
        return tbl.get("image_path"), tbl.get("caption")

    return None, None


def _fallback_slides(paper: dict) -> list:
    """Create basic slides if LLM fails."""
    slides = []
    order = 1

    slides.append({
        "slide_type": "title",
        "title": paper["title"],
        "subtitle": f"{', '.join(paper['authors'][:3])} — {date.today().strftime('%B %Y')}",
        "body_points": [f"ArXiv: {paper['arxiv_id']}"],
        "speaker_notes": f"This presentation covers the paper '{paper['title']}' by {', '.join(paper['authors'][:3])}.",
        "order": order,
    })
    order += 1

    slides.append({
        "slide_type": "problem",
        "title": "Paper Overview",
        "subtitle": "Abstract Summary",
        "body_points": [paper["abstract"][:500]],
        "speaker_notes": "This slide provides an overview of the paper's abstract and key findings.",
        "order": order,
    })
    order += 1

    for slide_type in ["methodology", "experiments", "results", "conclusion"]:
        slides.append({
            "slide_type": slide_type,
            "title": slide_type.title(),
            "body_points": ["Content extraction failed - please regenerate with a different model"],
            "speaker_notes": "This slide was auto-generated as a fallback.",
            "order": order,
        })
        order += 1

    return slides
