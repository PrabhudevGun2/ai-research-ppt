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

# Audience personas
AUDIENCE_PROFILES = {
    "executive": {
        "role": "Executive / Manager — Non-technical business leaders who need the big picture",
        "tone": (
            "AUDIENCE RULES:\n"
            "- NO math formulas, NO code, NO Greek letters, NO variable names\n"
            "- Translate every technical concept into a business analogy or plain English\n"
            "- Focus on: What problem is solved? What's the impact? Why does it matter?\n"
            "- Use concrete outcomes: 'cuts processing time in half' not 'O(n) vs O(n^2)'\n"
            "- Speaker notes should explain concepts as if presenting to a CEO\n"
            "- Frame results as ROI, competitive advantage, or strategic opportunity"
        ),
        "focus": "FOCUS on problem/impact (40%), results/outcomes (40%), methodology at a high level (20%). Skip ablation details.",
        "language": "Use plain English only. If a technical term is unavoidable, define it in parentheses — e.g., 'attention mechanism (a way for AI to focus on relevant parts of text)'.",
        "methodology_guidance": "2-3 slides explaining the approach using analogies and plain language. NO formulas. USE FIGURES — they tell the story visually.",
        "results_guidance": "3-4 slides focused on outcomes and impact. Use comparisons like 'X% better than existing methods'. USE TABLES for clear before/after comparisons.",
        "examples": (
            "BULLET POINT EXAMPLES for this audience:\n"
            "- GOOD: 'New method translates languages 10x faster than previous best'\n"
            "- BAD: 'Achieves 28.4 BLEU on WMT 2014 EN-DE benchmark'\n"
            "- GOOD: 'AI learns what to pay attention to in text, like a human skimming a document'\n"
            "- BAD: 'Multi-head self-attention computes Q, K, V projections across h parallel heads'\n"
            "- GOOD: 'Trained in 3.5 days on standard hardware — previously took months'\n"
            "- BAD: 'Training on 8x P100 GPUs for 300K steps with 0.1 dropout'"
        ),
    },
    "fresher": {
        "role": "AI/ML Student or Fresher — Early-career engineers learning the field",
        "tone": (
            "AUDIENCE RULES:\n"
            "- ALWAYS explain WHY before WHAT — give intuition before details\n"
            "- Define every acronym and technical term on first use\n"
            "- Use 'Think of it like...' analogies for complex concepts\n"
            "- Math formulas are OK but MUST be preceded by a plain-English explanation\n"
            "- Speaker notes should teach the concept, not just describe it\n"
            "- Connect ideas to things freshers already know (basic ML, Python, etc.)"
        ),
        "focus": "FOCUS on building understanding: problem (20%), methodology explained step-by-step (50%), results with context (20%), takeaways (10%).",
        "language": "Explain jargon on first use. Example: 'self-attention (the model decides which words in a sentence are most relevant to each other)'. Use analogies freely.",
        "methodology_guidance": "3-5 slides that teach the method step by step. Explain each component with intuition FIRST, then specifics. USE FIGURES to show architecture visually.",
        "results_guidance": "2-3 slides. Explain what the metrics mean before showing numbers. E.g., 'BLEU score measures translation quality (higher = better)' then show the result.",
        "examples": (
            "BULLET POINT EXAMPLES for this audience:\n"
            "- GOOD: 'Self-attention: each word \"looks at\" every other word to understand context'\n"
            "- BAD: 'Attention(Q,K,V) = softmax(QK^T/sqrt(d_k))V'\n"
            "- GOOD: 'BLEU score (translation quality metric, higher = better): 28.4 — best ever at the time'\n"
            "- BAD: '28.4 BLEU on WMT 2014 EN-DE, +2.0 over previous SOTA'\n"
            "- GOOD: 'Think of attention like highlighting — the model highlights important words automatically'\n"
            "- BAD: 'Multi-head attention projects into h subspaces with d_k dimensionality'"
        ),
    },
    "engineer": {
        "role": "AI/ML Engineer — Practitioners who build and deploy models",
        "tone": (
            "AUDIENCE RULES:\n"
            "- Be technical and specific — engineers want implementation details\n"
            "- Include exact hyperparameters, architecture choices, training details\n"
            "- Focus on: What can I use? How does it work? What are the tradeoffs?\n"
            "- Formulas OK but emphasize practical implications over theory\n"
            "- Speaker notes should cover practical considerations and gotchas"
        ),
        "focus": "FOCUS on methodology and architecture (40%), results and comparisons (30%), practical takeaways (20%), limitations (10%).",
        "language": "Technical language is fine. Be specific with numbers, names, metrics. No need to define standard ML terms.",
        "methodology_guidance": "3-5 slides covering architecture, key techniques, training setup with exact hyperparameters. USE FIGURES HERE.",
        "results_guidance": "3-5 slides with quantitative results, benchmark comparisons, and exact numbers. USE TABLES HERE.",
        "examples": (
            "BULLET POINT EXAMPLES for this audience:\n"
            "- GOOD: 'Transformer achieves 28.4 BLEU on EN-DE, +2.0 over previous SOTA'\n"
            "- BAD: 'The proposed architecture demonstrates significant improvements in translation'\n"
            "- GOOD: '8 attention heads, d_model=512, d_ff=2048, dropout=0.1'\n"
            "- BAD: 'The model uses several attention heads with a certain dimensionality'"
        ),
    },
    "researcher": {
        "role": "AI Researcher — Academics and research scientists",
        "tone": (
            "AUDIENCE RULES:\n"
            "- Full technical depth — equations, proofs, ablation analysis\n"
            "- Position this work relative to prior art and concurrent work\n"
            "- Highlight novel contributions vs incremental improvements\n"
            "- Speaker notes should discuss implications for future research\n"
            "- Be precise about experimental setup and statistical significance"
        ),
        "focus": "FOCUS on novelty and contributions (20%), methodology in full depth (40%), experimental rigor (30%), open questions (10%).",
        "language": "Full academic language. Include mathematical formulations. Reference specific prior work by name.",
        "methodology_guidance": "3-5 slides with full technical detail: architecture, loss functions, optimization, theoretical justification. USE FIGURES HERE.",
        "results_guidance": "3-5 slides: quantitative comparisons with SOTA, ablation studies, statistical analysis. USE TABLES HERE. Include exact numbers and confidence intervals if available.",
        "examples": (
            "BULLET POINT EXAMPLES for this audience:\n"
            "- GOOD: 'Attention(Q,K,V) = softmax(QK^T/sqrt(d_k))V — dot-product scales better than additive (Bahdanau 2015)'\n"
            "- BAD: 'Uses a type of attention mechanism'\n"
            "- GOOD: 'Ablation: single-head attention drops 0.9 BLEU; h=16 with d_k=32 also degrades'\n"
            "- BAD: 'Different configurations were tested'"
        ),
    },
}


def _get_audience_instructions(audience: str) -> dict:
    """Return audience-specific prompt instructions."""
    return AUDIENCE_PROFILES.get(audience, AUDIENCE_PROFILES["engineer"])


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

    audience = state.get("audience", "engineer")
    audience_instructions = _get_audience_instructions(audience)

    prompt = f"""You are creating a CONCISE, VISUAL slide deck for the following audience:

TARGET AUDIENCE: {audience_instructions['role']}

{audience_instructions['tone']}

PAPER CONTENT:
{paper_content}

CRITICAL RULES - READ CAREFULLY:
1. Keep bullet points SHORT: 10-20 words max per bullet. No walls of text.
2. Use 3-5 bullet points per slide, not more.
3. {audience_instructions['focus']}
4. Every figure and table from the paper MUST appear on a slide.
5. Speaker notes carry the detailed explanation (100-200 words).
6. {audience_instructions['language']}

AVAILABLE VISUALS: {n_figures} figures, {n_tables} tables.
You MUST use ALL of them. Assign each to a slide via "recommended_figure".

SLIDE STRUCTURE (exactly {TARGET_SLIDES} slides):

1. **Title** - Paper title, authors, date, arxiv link (1 slide)
2. **Problem & Motivation** - What problem, why it matters (1 slide)
3. **Key Contributions** - 3-5 main contributions as short bullets (1 slide)
4. **Methodology** - {audience_instructions['methodology_guidance']}
5. **Results & Comparisons** - {audience_instructions['results_guidance']}
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

{audience_instructions['examples']}

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
