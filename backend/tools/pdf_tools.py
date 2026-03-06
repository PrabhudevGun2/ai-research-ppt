"""
PDF extraction tools for figures, tables, and equations.
Uses OCR and structure analysis - no external APIs needed.
"""
import os
import io
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import fitz  # pymupdf
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ExtractedFigure:
    """Represents an extracted figure or table from a PDF."""
    figure_type: str  # "figure", "table", "equation"
    page_num: int
    image_path: str  # Path to saved image
    caption: str
    text_content: str  # OCR'd text if applicable
    bbox: tuple  # (x0, y0, x1, y1)


def download_arxiv_pdf(arxiv_id: str, output_dir: str = "/tmp/papers") -> Optional[str]:
    """Download a PDF from ArXiv."""
    import requests

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{arxiv_id}.pdf")

    if os.path.exists(file_path):
        return file_path

    # Try multiple ArXiv URLs
    urls = [
        f"https://arxiv.org/pdf/{arxiv_id}.pdf",
        f"https://arxiv.org/pdf/{arxiv_id}",
    ]

    for url in urls:
        try:
            response = requests.get(url, timeout=60, stream=True)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Downloaded PDF: {arxiv_id}")
                return file_path
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {e}")

    logger.error(f"Failed to download PDF for {arxiv_id}")
    return None


# ---------------------------------------------------------------------------
# Block-level helpers
# ---------------------------------------------------------------------------

def _get_sorted_blocks(page) -> List[dict]:
    """Get text blocks sorted by vertical position."""
    blocks = page.get_text("dict")["blocks"]
    return sorted(blocks, key=lambda b: b.get("bbox", (0, 0, 0, 0))[1])


def _block_text(block: dict) -> str:
    """Extract plain text from a block."""
    if block.get("type") != 0:
        return ""
    text = ""
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text += span.get("text", "")
        text += "\n"
    return text.strip()


def _block_has_math_font(block: dict) -> bool:
    """Check if any span in the block uses a math font."""
    if block.get("type") != 0:
        return False
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            font = span.get("font", "").lower()
            if any(f in font for f in ["cmr", "cmmi", "cmsy", "cmex", "math", "symbol"]):
                return True
    return False


def _is_section_header(text: str) -> bool:
    """Check if text looks like a section header."""
    t = text.strip()
    # "3.5 Positional Encoding", "7 Conclusion", "A. Appendix", etc.
    if re.match(r'^[A-Z\d]+[\.\s]', t) and len(t) < 80:
        return True
    if re.match(r'^\d+(\.\d+)*\s+[A-Z]', t):
        return True
    return False


def _find_content_boundary(blocks: List[dict], start_y: float, page_height: float,
                           stop_patterns: List[str] = None) -> float:
    """
    Find where content ends below start_y.
    Stops at: next TABLE/Figure caption, section header, or large vertical gap.
    """
    if stop_patterns is None:
        stop_patterns = [
            r'^(TABLE\s+[IVXLCDM\d]+)',
            r'^(Fig\.?\s*\d+|Figure\s*\d+)\s*[:.]\s',
            r'^References\s*$',
        ]

    prev_bottom = start_y
    content_bottom = start_y

    for block in blocks:
        bbox = block.get("bbox", (0, 0, 0, 0))
        if bbox[1] <= start_y:
            continue

        text = _block_text(block)
        if not text:
            continue

        # Check stop patterns
        for pat in stop_patterns:
            if re.match(pat, text, re.IGNORECASE):
                return bbox[1] - 5

        # Check section header
        if _is_section_header(text) and bbox[1] > start_y + 30:
            return bbox[1] - 5

        # Large vertical gap (>40pt) suggests end of table/figure region
        if bbox[1] - prev_bottom > 40 and content_bottom > start_y + 20:
            return content_bottom + 5

        prev_bottom = bbox[3]
        content_bottom = bbox[3]

    return min(content_bottom + 10, page_height)


# ---------------------------------------------------------------------------
# Figure extraction
# ---------------------------------------------------------------------------

def extract_figures_from_pdf(pdf_path: str, output_dir: str, min_size: int = 100) -> List[ExtractedFigure]:
    """
    Extract figures from a PDF using two strategies:
    1. Find figure captions at block level and render the figure region
    2. Extract embedded images as fallback for pages without caption-based figures
    """
    os.makedirs(output_dir, exist_ok=True)
    figures = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    try:
        doc = fitz.open(pdf_path)

        # Strategy 1: Block-level caption detection (high quality)
        caption_figures = _extract_figures_by_caption(doc, output_dir, base_name)
        caption_pages = {cf.page_num for cf in caption_figures}
        figures.extend(caption_figures)

        # Strategy 2: Embedded images for pages without caption-based figures
        for page_num in range(len(doc)):
            if (page_num + 1) in caption_pages:
                continue  # Already have caption-based figure for this page

            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_idx, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        img_bytes = base_image["image"]
                        img_ext = base_image["ext"]

                        pil_image = Image.open(io.BytesIO(img_bytes))
                        width, height = pil_image.size

                        if width < min_size or height < min_size:
                            continue

                        img_filename = f"{base_name}_p{page_num+1}_fig{img_idx+1}.{img_ext}"
                        img_path = os.path.join(output_dir, img_filename)

                        with open(img_path, "wb") as f:
                            f.write(img_bytes)

                        caption = _find_caption(page, img_info)

                        figures.append(ExtractedFigure(
                            figure_type="figure",
                            page_num=page_num + 1,
                            image_path=img_path,
                            caption=caption,
                            text_content="",
                            bbox=(0, 0, width, height),
                        ))

                except Exception as e:
                    logger.warning(f"Error extracting image {img_idx} from page {page_num}: {e}")

        doc.close()

    except Exception as e:
        logger.error(f"Error opening PDF {pdf_path}: {e}")

    return figures


def _extract_figures_by_caption(doc, output_dir: str, base_name: str) -> List[ExtractedFigure]:
    """
    Find figure captions at the TEXT BLOCK level (not inline references).
    A true caption is a block whose text starts with "Figure N:" or "Fig. N:".
    Then render the region above the caption (the figure itself).
    """
    figures = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = _get_sorted_blocks(page)
        page_rect = page.rect

        for block in blocks:
            text = _block_text(block)
            if not text:
                continue

            # Must START the block text - this eliminates inline references
            m = re.match(r'(Fig\.?\s*\d+|Figure\s*\d+)\s*[:.]\s*(.*)', text, re.IGNORECASE | re.DOTALL)
            if not m:
                continue

            fig_label = m.group(1).strip()
            caption_text = text[:200]
            bbox = block.get("bbox", (0, 0, 0, 0))
            cap_y_top = bbox[1]

            # Figure is ABOVE the caption - find where it starts
            # Look at blocks above to find the figure region
            y_start = _find_figure_top(blocks, cap_y_top, page_rect)
            y_end = min(bbox[3] + 5, page_rect.height)  # Include caption

            # Ensure minimum region height
            if cap_y_top - y_start < 30:
                y_start = max(cap_y_top - 200, 0)

            clip_rect = fitz.Rect(0, y_start, page_rect.width, y_end)
            mat = fitz.Matrix(3, 3)  # 3x zoom
            pix = page.get_pixmap(matrix=mat, clip=clip_rect)

            safe_label = re.sub(r'[^a-zA-Z0-9]', '', fig_label)
            img_filename = f"{base_name}_p{page_num+1}_{safe_label}.png"
            img_path = os.path.join(output_dir, img_filename)
            pix.save(img_path)

            if os.path.exists(img_path) and os.path.getsize(img_path) > 2000:
                figures.append(ExtractedFigure(
                    figure_type="figure",
                    page_num=page_num + 1,
                    image_path=img_path,
                    caption=caption_text,
                    text_content="",
                    bbox=(0, y_start, page_rect.width, y_end),
                ))
                logger.info(f"Extracted figure: {fig_label} from page {page_num+1}")

    return figures


def _find_figure_top(blocks: List[dict], caption_y: float, page_rect) -> float:
    """
    Find where the figure region starts above a caption.
    Walk upward from the caption and look for a text block that belongs to
    normal body text (not part of the figure). The figure starts just after that block.
    """
    # Collect blocks above the caption, sorted top-to-bottom
    above_blocks = []
    for b in blocks:
        bbox = b.get("bbox", (0, 0, 0, 0))
        if bbox[3] < caption_y:
            text = _block_text(b)
            above_blocks.append((bbox, text))

    if not above_blocks:
        return max(caption_y - 300, 0)

    # Walk from closest-to-caption upward
    above_blocks.sort(key=lambda x: x[0][1], reverse=True)

    for bbox, text in above_blocks:
        # If this is a substantial text paragraph (not a label), the figure starts below it
        if text and len(text) > 60 and not re.match(r'^(Fig|Table|Attention)', text, re.IGNORECASE):
            return bbox[3] + 2  # Figure starts just below this text

        # Section header also marks boundary
        if text and _is_section_header(text):
            return bbox[3] + 2

    # Fallback: use a reasonable region size
    return max(caption_y - 350, 0)


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------

def extract_tables_from_pdf(pdf_path: str, output_dir: str) -> List[ExtractedFigure]:
    """
    Extract tables from a PDF using two strategies:
    1. Find TABLE captions at block level and render bounded table regions
    2. Fall back to pdfplumber structural extraction
    """
    os.makedirs(output_dir, exist_ok=True)
    tables = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Strategy 1: Caption-based table extraction with proper boundaries
    try:
        tables_from_text = _extract_tables_by_caption(pdf_path, output_dir, base_name)
        tables.extend(tables_from_text)
    except Exception as e:
        logger.warning(f"Table-by-caption extraction failed: {e}")

    # Strategy 2: pdfplumber structural extraction (for tables without captions)
    if not tables:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()

                    for table_idx, table_data in enumerate(page_tables):
                        if not table_data or len(table_data) < 2:
                            continue

                        table_text = _format_table_text(table_data)
                        img_filename = f"{base_name}_p{page_num+1}_tbl{table_idx+1}.png"
                        img_path = os.path.join(output_dir, img_filename)
                        _render_table_image(table_data, img_path)

                        tables.append(ExtractedFigure(
                            figure_type="table",
                            page_num=page_num + 1,
                            image_path=img_path,
                            caption=f"Table with {len(table_data)} rows",
                            text_content=table_text,
                            bbox=(0, 0, 0, 0),
                        ))
        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path}: {e}")

    return tables


def _extract_tables_by_caption(pdf_path: str, output_dir: str, base_name: str) -> List[ExtractedFigure]:
    """
    Find table regions by locating TABLE captions at the block level,
    then use _find_content_boundary to determine where the table ends.
    """
    tables = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = _get_sorted_blocks(page)
        page_rect = page.rect

        # Find TABLE caption blocks
        table_captions = []
        for block in blocks:
            text = _block_text(block)
            m = re.match(r'(TABLE\s+[IVXLCDM\d]+)\s*[:.]', text, re.IGNORECASE)
            if m:
                bbox = block.get("bbox", (0, 0, 0, 0))
                table_captions.append((bbox, text[:200]))

        if not table_captions:
            continue

        for cap_idx, (cap_bbox, caption) in enumerate(table_captions):
            y_start = max(cap_bbox[1] - 5, 0)

            # Find table end boundary
            if cap_idx + 1 < len(table_captions):
                # Next table on same page
                y_end = table_captions[cap_idx + 1][0][1] - 10
            else:
                # Use content boundary detection
                y_end = _find_content_boundary(blocks, cap_bbox[3], page_rect.height)

            # Clamp and ensure minimum size
            y_end = min(y_end, page_rect.height)
            if y_end - y_start < 40:
                y_end = min(y_start + 200, page_rect.height)

            clip_rect = fitz.Rect(0, y_start, page_rect.width, y_end)
            mat = fitz.Matrix(3, 3)
            pix = page.get_pixmap(matrix=mat, clip=clip_rect)

            img_filename = f"{base_name}_p{page_num+1}_table{cap_idx+1}.png"
            img_path = os.path.join(output_dir, img_filename)
            pix.save(img_path)

            if os.path.exists(img_path) and os.path.getsize(img_path) > 1000:
                tables.append(ExtractedFigure(
                    figure_type="table",
                    page_num=page_num + 1,
                    image_path=img_path,
                    caption=caption,
                    text_content="",
                    bbox=(0, y_start, page_rect.width, y_end),
                ))
                logger.info(f"Extracted table: {caption[:60]} -> {img_path}")

    doc.close()
    return tables


# ---------------------------------------------------------------------------
# Equation extraction
# ---------------------------------------------------------------------------

def extract_equation_regions(pdf_path: str, output_dir: str) -> List[ExtractedFigure]:
    """
    Extract numbered equations by finding math-font blocks that end with (N).
    Captures the full equation region including multi-line formulas.
    """
    os.makedirs(output_dir, exist_ok=True)
    equations = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = _get_sorted_blocks(page)
            page_rect = page.rect

            # Pass 1: Find blocks with equation numbers like (1), (2), ...
            eq_anchor_blocks = []
            for block in blocks:
                text = _block_text(block)
                if not text:
                    continue
                # Equation number at end of block
                m = re.search(r'\((\d{1,2})\)\s*$', text)
                if m and _block_has_math_font(block) and len(text) < 300:
                    eq_num = m.group(1)
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    eq_anchor_blocks.append((bbox, eq_num, text))

            # Pass 2: For each numbered equation, find the full equation region
            # (may include blocks above that are part of the same formula)
            for anchor_bbox, eq_num, anchor_text in eq_anchor_blocks:
                # Look for math-font blocks directly above that are part of this equation
                region_top = anchor_bbox[1]
                for block in reversed(blocks):
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    # Block must be just above our current region top
                    if bbox[3] < region_top and (region_top - bbox[3]) < 15:
                        if _block_has_math_font(block):
                            text = _block_text(block)
                            if text and len(text) < 200:
                                region_top = bbox[1]
                        else:
                            break
                    elif bbox[3] < region_top - 15:
                        break

                # Add padding
                y_start = max(region_top - 8, 0)
                y_end = min(anchor_bbox[3] + 8, page_rect.height)

                clip_rect = fitz.Rect(
                    max(page_rect.width * 0.1, 0),  # Slight left margin
                    y_start,
                    min(page_rect.width * 0.9, page_rect.width),
                    y_end
                )
                mat = fitz.Matrix(4, 4)  # 4x zoom for crisp equations
                pix = page.get_pixmap(matrix=mat, clip=clip_rect)

                img_filename = f"{base_name}_p{page_num+1}_eq{eq_num}.png"
                img_path = os.path.join(output_dir, img_filename)
                pix.save(img_path)

                if os.path.exists(img_path) and os.path.getsize(img_path) > 500:
                    equations.append(ExtractedFigure(
                        figure_type="equation",
                        page_num=page_num + 1,
                        image_path=img_path,
                        caption=f"Equation ({eq_num})",
                        text_content=anchor_text.strip(),
                        bbox=(clip_rect.x0, y_start, clip_rect.x1, y_end),
                    ))
                    logger.info(f"Extracted equation ({eq_num}) from page {page_num+1}")

        doc.close()

    except Exception as e:
        logger.error(f"Error extracting equations from {pdf_path}: {e}")

    return equations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_caption(page, img_info) -> str:
    """Try to find caption text near an image."""
    try:
        # Get image bounding box
        bbox = None
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") == 1:  # Image block
                if block.get("image") == img_info[0]:
                    bbox = block.get("bbox")
                    break

        if not bbox:
            return ""

        # Look for text below the image
        text_blocks = page.get_text("dict")["blocks"]
        captions = []

        for block in text_blocks:
            if block.get("type") != 0:
                continue
            block_bbox = block.get("bbox")
            if not block_bbox:
                continue

            if block_bbox[1] > bbox[3]:
                if abs(block_bbox[0] - bbox[0]) < 50:
                    text = _block_text(block)
                    if text:
                        captions.append(text)

        for cap in captions:
            if re.match(r"^(Figure|Fig\.|Table)\s*\d*", cap, re.I):
                return cap[:200]

        return captions[0][:200] if captions else ""

    except Exception:
        return ""


def _format_table_text(table_data: List[List[str]]) -> str:
    """Format table data as text."""
    if not table_data:
        return ""

    lines = []
    for row in table_data:
        cells = [str(cell) if cell else "" for cell in row]
        lines.append(" | ".join(cells))

    return "\n".join(lines)


def _render_table_image(table_data: List[List[str]], output_path: str):
    """Render table as an image."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        rows = len(table_data)
        cols = max(len(row) for row in table_data) if table_data else 0

        if rows == 0 or cols == 0:
            return

        cell_width = 150
        cell_height = 30
        margin = 20

        img_width = cols * cell_width + 2 * margin
        img_height = rows * cell_height + 2 * margin

        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except Exception:
            font = ImageFont.load_default()

        for row_idx, row in enumerate(table_data):
            for col_idx, cell in enumerate(row):
                x = margin + col_idx * cell_width + 5
                y = margin + row_idx * cell_height + 5
                text = str(cell)[:25] if cell else ""
                draw.text((x, y), text, fill="black", font=font)

        for i in range(rows + 1):
            y = margin + i * cell_height
            draw.line([(margin, y), (img_width - margin, y)], fill="gray", width=1)

        for j in range(cols + 1):
            x = margin + j * cell_width
            draw.line([(x, margin), (x, img_height - margin)], fill="gray", width=1)

        img.save(output_path)

    except Exception as e:
        logger.warning(f"Error rendering table image: {e}")


def get_best_figures_for_ppt(
    figures: List[ExtractedFigure],
    max_figures: int = 5,
    prefer_tables: bool = True
) -> List[ExtractedFigure]:
    """
    Select the best figures/tables to include in PPT.
    Prioritizes tables with data and figures with captions.
    """
    scored = []

    for fig in figures:
        score = 0

        if fig.figure_type == "table":
            score += 10 if prefer_tables else 5

        if fig.caption:
            score += 5

        if fig.bbox:
            width = fig.bbox[2] - fig.bbox[0]
            height = fig.bbox[3] - fig.bbox[1]
            if width > 300 and height > 200:
                score += 3

        scored.append((score, fig))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [fig for _, fig in scored[:max_figures]]
