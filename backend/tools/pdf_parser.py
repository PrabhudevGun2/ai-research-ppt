"""
PDF text extraction and section parsing.
"""
import re
import logging
from typing import Dict, List, Any

import fitz  # pymupdf

logger = logging.getLogger(__name__)


def extract_paper_content(pdf_path: str) -> Dict[str, Any]:
    """
    Extract structured content from a research paper PDF.

    Returns:
        dict with 'full_text', 'sections', and metadata
    """
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        all_pages = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            all_pages.append(text)
            full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n{text}"

        doc.close()

        # Try to parse sections
        sections = parse_sections(full_text)

        return {
            "full_text": full_text,
            "sections": sections,
            "page_count": len(all_pages),
        }

    except Exception as e:
        logger.error(f"Error extracting content from {pdf_path}: {e}")
        return {
            "full_text": "",
            "sections": {},
            "page_count": 0,
        }


def parse_sections(text: str) -> Dict[str, str]:
    """
    Parse paper text into sections.

    Looks for common section headers like:
    - Abstract
    - Introduction
    - Related Work
    - Method/Methodology
    - Experiments/Experimental Setup
    - Results
    - Discussion
    - Conclusion
    - References
    """
    sections = {}

    # Common section patterns (case-insensitive)
    section_patterns = [
        (r'\n\s*Abstract\s*\n', 'abstract'),
        (r'\n\s*1\.?\s*Introduction\s*\n', 'introduction'),
        (r'\n\s*2\.?\s*Related\s*Work\s*\n', 'related_work'),
        (r'\n\s*2\.?\s*Background\s*\n', 'background'),
        (r'\n\s*3\.?\s*Method\s*\n', 'method'),
        (r'\n\s*3\.?\s*Methodology\s*\n', 'methodology'),
        (r'\n\s*3\.?\s*Approach\s*\n', 'approach'),
        (r'\n\s*4\.?\s*Experiments\s*\n', 'experiments'),
        (r'\n\s*4\.?\s*Experimental\s*Setup\s*\n', 'experiments'),
        (r'\n\s*5\.?\s*Results\s*\n', 'results'),
        (r'\n\s*5\.?\s*Evaluation\s*\n', 'evaluation'),
        (r'\n\s*6\.?\s*Discussion\s*\n', 'discussion'),
        (r'\n\s*6\.?\s*Analysis\s*\n', 'analysis'),
        (r'\n\s*7\.?\s*Conclusion\s*\n', 'conclusion'),
        (r'\n\s*Conclusion[s]?\s*\n', 'conclusion'),
        (r'\n\s*Limitations\s*\n', 'limitations'),
        (r'\n\s*Future\s*Work\s*\n', 'future_work'),
        (r'\n\s*References\s*\n', 'references'),
        (r'\n\s*Bibliography\s*\n', 'references'),
    ]

    # Find all section positions
    section_positions = []

    for pattern, section_name in section_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            section_positions.append((match.start(), match.end(), section_name))

    # Sort by position
    section_positions.sort(key=lambda x: x[0])

    # Extract section content
    for i, (start, end, name) in enumerate(section_positions):
        # Find end of this section (start of next section or end of text)
        if i + 1 < len(section_positions):
            section_end = section_positions[i + 1][0]
        else:
            section_end = len(text)

        content = text[end:section_end].strip()

        # Only include if substantial content
        if len(content) > 100:
            sections[name] = content[:5000]  # Limit section size

    return sections


def extract_key_sentences(text: str, max_sentences: int = 20) -> List[str]:
    """
    Extract key sentences from paper text.
    Uses simple heuristics to find important sentences.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Filter out very short or very long sentences
    sentences = [s.strip() for s in sentences if 20 < len(s) < 500]

    # Score sentences by indicators
    scored = []
    for s in sentences:
        score = 0
        lower_s = s.lower()

        # Boost for key phrases
        if any(phrase in lower_s for phrase in [
            'we propose', 'we present', 'we introduce', 'our approach',
            'this paper', 'our method', 'we show', 'we demonstrate',
            'significantly outperforms', 'state-of-the-art', 'novel',
            'achieves', 'improves', 'contribution'
        ]):
            score += 3

        # Boost for numbers (quantitative claims)
        if re.search(r'\d+\.?\d*%', s):
            score += 2

        # Boost for equations or technical content
        if '=' in s and any(c in s for c in 'αβγδεζηθικλμνξπρστυφχψω'):
            score += 1

        scored.append((score, s))

    # Sort by score and return top sentences
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_sentences]]
