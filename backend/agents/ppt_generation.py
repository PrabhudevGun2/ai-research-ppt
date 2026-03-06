"""
PPT Generation agent - creates professional PowerPoint with images and tables.
Also generates a companion Word document with full verbose content.
"""
import os
import logging
from datetime import date

from backend.graph.state import ResearchState, Stage, SlideContent, GeneratedPPT
from backend.tools.pptx_tools import (
    create_presentation, set_slide_background, add_header_bar,
    add_bullet_points, add_accent_line, add_page_number, add_footer,
    add_image_to_slide, DARK_BLUE, WHITE, LIGHT_GRAY, ACCENT_BLUE,
)
from backend.config import settings
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

logger = logging.getLogger(__name__)

# Color scheme
DARK_BLUE = RGBColor(0x1A, 0x23, 0x7E)
ACCENT_BLUE = RGBColor(0x42, 0xA5, 0xF5)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PROBLEM_RED = RGBColor(0xC6, 0x28, 0x28)
METHOD_GREEN = RGBColor(0x2E, 0x7D, 0x32)
RESULTS_BLUE = RGBColor(0x15, 0x65, 0xC0)


def _add_title_slide(prs, content: SlideContent, num: int, total: int):
    """Title slide - clean and professional."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_BLUE)

    # Title
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(2.0), Inches(12.33), Inches(2.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = content["title"]
    p.font.size = Pt(40)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    if content.get("subtitle"):
        sub_box = slide.shapes.add_textbox(Inches(0.5), Inches(4.2), Inches(12.33), Inches(1.0))
        stf = sub_box.text_frame
        sp = stf.paragraphs[0]
        sp.text = content["subtitle"]
        sp.font.size = Pt(20)
        sp.font.color.rgb = ACCENT_BLUE
        sp.alignment = PP_ALIGN.CENTER

    # Date and arxiv info
    if content.get("body_points"):
        info_box = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12.33), Inches(1.0))
        itf = info_box.text_frame
        for i, point in enumerate(content["body_points"][:2]):
            ip = itf.paragraphs[0] if i == 0 else itf.add_paragraph()
            ip.text = point
            ip.font.size = Pt(14)
            ip.font.color.rgb = RGBColor(0xB0, 0xBE, 0xC5)
            ip.alignment = PP_ALIGN.CENTER

    add_page_number(slide, num, total)


def _add_content_slide_with_image(prs, content: SlideContent, num: int, total: int, accent_color=None):
    """Content slide with optional image on the right side."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, LIGHT_GRAY)

    add_header_bar(slide, content["title"], content.get("subtitle"))

    # Add accent line
    if accent_color:
        line = slide.shapes.add_shape(1, Inches(0.5), Inches(1.45), Inches(12.33), Pt(4))
        line.fill.solid()
        line.fill.fore_color.rgb = accent_color
        line.line.fill.background()

    # Check if we have an image
    image_path = content.get("image_path")
    has_valid_image = image_path and os.path.exists(image_path)

    if has_valid_image:
        # Two-column layout: text on left, image on right
        # NOTE: add_bullet_points expects raw floats (inches), NOT Inches() objects
        add_bullet_points(
            slide, content["body_points"],
            font_size=14, top=1.7,
            left=0.4, width=6.5
        )

        # add_image_to_slide expects Inches() objects for positioning
        try:
            add_image_to_slide(slide, image_path, left=Inches(7.2), top=Inches(1.7),
                             max_width=Inches(5.5), max_height=Inches(5.0))
        except Exception as e:
            logger.warning(f"Failed to add image {image_path}: {e}")
    else:
        # Full-width text
        add_bullet_points(slide, content["body_points"], font_size=16, top=1.8)

    add_page_number(slide, num, total)

    footer_text = content.get("topic") or content.get("subtitle") or "Technical Presentation"
    if footer_text and isinstance(footer_text, str):
        add_footer(slide, footer_text[:50])


def _add_problem_slide(prs, content: SlideContent, num: int, total: int):
    _add_content_slide_with_image(prs, content, num, total, accent_color=PROBLEM_RED)


def _add_methodology_slide(prs, content: SlideContent, num: int, total: int):
    _add_content_slide_with_image(prs, content, num, total, accent_color=METHOD_GREEN)


def _add_results_slide(prs, content: SlideContent, num: int, total: int):
    _add_content_slide_with_image(prs, content, num, total, accent_color=RESULTS_BLUE)


def _add_equation_slide(prs, content: SlideContent, num: int, total: int):
    """Equation slide - prominent, centered display."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, LIGHT_GRAY)

    add_header_bar(slide, content["title"], "Mathematical Formulation")

    image_path = content.get("image_path")
    if image_path and os.path.exists(image_path):
        try:
            add_image_to_slide(slide, image_path, left=Inches(1.0), top=Inches(2.0),
                             max_width=Inches(11.0), max_height=Inches(3.5))
            if content["body_points"]:
                add_bullet_points(slide, content["body_points"], font_size=14,
                                top=5.5, left=0.5, width=12.0)
        except Exception as e:
            logger.warning(f"Failed to add equation image: {e}")
            _add_equation_text(slide, content)
    else:
        _add_equation_text(slide, content)

    add_page_number(slide, num, total)
    add_footer(slide, "Key Equations")


def _add_equation_text(slide, content: SlideContent):
    """Display equations as text (fallback)."""
    y_pos = Inches(1.8)
    for point in content["body_points"][:5]:
        eq_box = slide.shapes.add_textbox(Inches(0.5), y_pos, Inches(12.33), Inches(0.8))
        tf = eq_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        clean_text = point.replace("$", "").replace("\\(", "").replace("\\)", "")
        p.text = clean_text
        p.font.size = Pt(18)
        p.font.name = "Courier New"
        p.font.color.rgb = DARK_BLUE
        p.alignment = PP_ALIGN.CENTER
        y_pos += Inches(0.7)


def _add_architecture_slide(prs, content: SlideContent, num: int, total: int):
    """Architecture slide - often has diagram."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, LIGHT_GRAY)

    add_header_bar(slide, content["title"], "System Architecture")

    image_path = content.get("image_path")
    if image_path and os.path.exists(image_path):
        try:
            add_image_to_slide(slide, image_path, left=Inches(1.0), top=Inches(1.6),
                             max_width=Inches(11.0), max_height=Inches(4.5))
            if content["body_points"]:
                add_bullet_points(slide, content["body_points"][:3], font_size=13,
                                top=6.2, left=0.5, width=12.0)
        except Exception as e:
            logger.warning(f"Failed to add architecture image: {e}")
            _add_content_slide_with_image(prs, content, num, total)
    else:
        _add_content_slide_with_image(prs, content, num, total)

    add_page_number(slide, num, total)
    add_footer(slide, "Architecture")


def _add_summary_slide(prs, content: SlideContent, num: int, total: int):
    """Summary/conclusion slide with dark background."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_BLUE)

    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(1.0), Inches(12.33), Inches(1.5))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = content["title"]
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    if content["body_points"]:
        points_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(11.33), Inches(4.0))
        ptf = points_box.text_frame
        for i, point in enumerate(content["body_points"][:8]):
            pp = ptf.paragraphs[0] if i == 0 else ptf.add_paragraph()
            pp.text = f"• {point}"
            pp.font.size = Pt(16)
            pp.font.color.rgb = ACCENT_BLUE
            pp.space_after = Pt(10)

    add_page_number(slide, num, total)


# Slide type handlers
SLIDE_HANDLERS = {
    "title": _add_title_slide,
    "problem": _add_problem_slide,
    "background": _add_content_slide_with_image,
    "contribution": _add_content_slide_with_image,
    "methodology": _add_methodology_slide,
    "method": _add_methodology_slide,
    "architecture": _add_architecture_slide,
    "equation": _add_equation_slide,
    "equations": _add_equation_slide,
    "algorithm": _add_content_slide_with_image,
    "experiments": _add_content_slide_with_image,
    "results": _add_results_slide,
    "evaluation": _add_results_slide,
    "analysis": _add_content_slide_with_image,
    "discussion": _add_content_slide_with_image,
    "limitations": _add_content_slide_with_image,
    "future": _add_content_slide_with_image,
    "conclusion": _add_summary_slide,
    "references": _add_content_slide_with_image,
    "content": _add_content_slide_with_image,
}


def _generate_word_document(session_id: str, slides: list, paper: dict) -> str:
    """Generate a detailed Word document companion to the PPT."""
    from docx import Document
    from docx.shared import Pt as DocxPt, Inches as DocxInches, RGBColor as DocxRGB
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Style adjustments
    style = doc.styles['Normal']
    style.font.size = DocxPt(11)
    style.font.name = 'Calibri'

    # Title page
    title_para = doc.add_heading(paper.get("title", "Research Paper Analysis"), level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata
    authors = paper.get("authors", [])
    if authors:
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = meta.add_run(f"Authors: {', '.join(authors[:10])}")
        run.font.size = DocxPt(12)
        run.font.color.rgb = DocxRGB(0x55, 0x55, 0x55)

    arxiv_id = paper.get("arxiv_id", "")
    if arxiv_id:
        meta2 = doc.add_paragraph()
        meta2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = meta2.add_run(f"ArXiv: {arxiv_id} | Generated: {date.today().strftime('%B %d, %Y')}")
        run.font.size = DocxPt(10)
        run.font.color.rgb = DocxRGB(0x88, 0x88, 0x88)

    doc.add_page_break()

    # Table of contents header
    doc.add_heading("Table of Contents", level=1)
    for i, slide in enumerate(slides):
        if slide.get("slide_type") == "title":
            continue
        toc_para = doc.add_paragraph(f"{i}. {slide.get('title', f'Section {i}')}")
        toc_para.style = doc.styles['List Number']

    doc.add_page_break()

    # Abstract
    abstract = paper.get("abstract", "")
    if abstract:
        doc.add_heading("Abstract", level=1)
        doc.add_paragraph(abstract)
        doc.add_paragraph()

    # Each slide becomes a detailed section
    for slide in slides:
        if slide.get("slide_type") == "title":
            continue

        slide_title = slide.get("title", "Section")
        doc.add_heading(slide_title, level=1)

        subtitle = slide.get("subtitle")
        if subtitle:
            sub_para = doc.add_paragraph()
            run = sub_para.add_run(subtitle)
            run.font.italic = True
            run.font.color.rgb = DocxRGB(0x44, 0x44, 0x44)

        # Body points as detailed paragraphs
        body_points = slide.get("body_points", [])
        for point in body_points:
            p = doc.add_paragraph(point, style='List Bullet')

        # Speaker notes as detailed prose
        notes = slide.get("speaker_notes")
        if notes:
            doc.add_paragraph()
            notes_heading = doc.add_paragraph()
            run = notes_heading.add_run("Detailed Notes:")
            run.bold = True
            run.font.size = DocxPt(11)
            doc.add_paragraph(notes)

        # Add image if available
        image_path = slide.get("image_path")
        if image_path and os.path.exists(image_path):
            try:
                doc.add_picture(image_path, width=DocxInches(5.5))
                caption = slide.get("image_caption", "")
                if caption:
                    cap_para = doc.add_paragraph(caption)
                    cap_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    cap_para.runs[0].font.italic = True
                    cap_para.runs[0].font.size = DocxPt(9)
            except Exception as e:
                logger.warning(f"Failed to add image to doc: {e}")

        doc.add_paragraph()  # spacing

    # Save
    doc_path = os.path.join(settings.output_dir, f"{session_id}.docx")
    doc.save(doc_path)
    logger.info(f"[{session_id}] Word document saved to {doc_path}")
    return doc_path


def ppt_generation_node(state: ResearchState) -> dict:
    """Generate comprehensive PPT and Word document from approved slides."""
    session_id = state["session_id"]
    approved_slides = state.get("approved_slides") or state.get("slide_contents", [])
    logger.info(f"[{session_id}] Generating PPT with {len(approved_slides)} slides")

    prs = create_presentation()
    total = len(approved_slides)

    for i, content in enumerate(approved_slides, start=1):
        slide_type = content.get("slide_type", "content")

        try:
            handler = SLIDE_HANDLERS.get(slide_type, _add_content_slide_with_image)
            handler(prs, content, i, total)
        except Exception as e:
            logger.error(f"[{session_id}] Error adding slide {i} ({slide_type}): {e}")
            _add_content_slide_with_image(prs, content, i, total)

    # Save PPT
    os.makedirs(settings.output_dir, exist_ok=True)
    file_path = os.path.join(settings.output_dir, f"{session_id}.pptx")
    prs.save(file_path)

    # Generate companion Word document
    paper = state.get("processed_paper") or state.get("selected_paper") or {}
    doc_path = None
    try:
        doc_path = _generate_word_document(session_id, approved_slides, paper)
    except Exception as e:
        logger.warning(f"[{session_id}] Word document generation failed: {e}")

    title = paper.get("title", "AI Research Presentation")

    generated_ppt: GeneratedPPT = {
        "file_path": file_path,
        "doc_path": doc_path,
        "session_id": session_id,
        "slide_count": len(approved_slides),
        "topics_covered": [title[:100]],
        "generated_at": date.today().isoformat(),
    }

    logger.info(f"[{session_id}] PPT saved to {file_path} with {len(approved_slides)} slides")

    # Clean up extracted assets (PDFs, images) - they're now embedded in pptx/docx
    assets_dir = os.path.join(settings.output_dir, session_id, "assets")
    if os.path.isdir(assets_dir):
        import shutil
        shutil.rmtree(assets_dir, ignore_errors=True)
        logger.info(f"[{session_id}] Cleaned up assets directory")

    return {
        "current_stage": Stage.AWAITING_FINAL_REVIEW,
        "generated_ppt": generated_ppt,
    }
