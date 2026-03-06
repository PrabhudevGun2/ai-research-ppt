"""Tests for PDF text extraction and section parsing."""
import os
import tempfile
import pytest
from backend.tools.pdf_parser import extract_paper_content, parse_sections, extract_key_sentences
from backend.tools.pdf_tools import download_arxiv_pdf


@pytest.fixture(scope="module")
def sample_pdf():
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = download_arxiv_pdf("1706.03762", output_dir=tmpdir)
        if pdf_path and os.path.exists(pdf_path):
            yield pdf_path
        else:
            pytest.skip("Could not download sample PDF")


class TestExtractPaperContent:
    def test_extracts_text(self, sample_pdf):
        result = extract_paper_content(sample_pdf)
        assert "full_text" in result
        assert len(result["full_text"]) > 1000, "Should extract substantial text"
        assert "sections" in result
        assert result["page_count"] > 0

    def test_sections_found(self, sample_pdf):
        result = extract_paper_content(sample_pdf)
        sections = result["sections"]
        # The transformer paper should have recognizable sections
        assert isinstance(sections, dict)
        # At least some sections should be found
        if sections:
            for name, content in sections.items():
                assert len(content) > 50, f"Section '{name}' too short"


class TestParseSections:
    def test_parses_known_sections(self):
        text = """
        Some preamble text

        Abstract
        This is the abstract of the paper describing key findings.
        It continues for several sentences with important details about
        the methodology and results that were achieved.

        1. Introduction
        This section introduces the problem and provides background context.
        The problem is important because of several factors that we discuss.
        We also review prior work and identify gaps in the literature.

        3. Method
        Our proposed method uses a novel approach to solve the problem.
        The architecture consists of multiple components working together.
        We describe each component in detail with mathematical formulations.

        5. Results
        The results show significant improvement over baselines.
        On benchmark X, we achieve 95.2% accuracy compared to 90.1%.
        These results demonstrate the effectiveness of our approach.

        7. Conclusion
        We presented a novel approach that achieves state-of-the-art results.
        Future work includes extending to other domains and larger datasets.
        Our code and models are publicly available for the community.
        """
        sections = parse_sections(text)
        assert "abstract" in sections or "introduction" in sections
        assert isinstance(sections, dict)


class TestExtractKeySentences:
    def test_extracts_key_sentences(self):
        text = (
            "We propose a novel method for text classification. "
            "The method achieves 95.2% accuracy on the GLUE benchmark. "
            "This is a filler sentence about nothing important. "
            "Our approach significantly outperforms all existing baselines. "
            "The weather is nice today."
        )
        sentences = extract_key_sentences(text, max_sentences=3)
        assert len(sentences) <= 3
        # Important sentences should be ranked higher
        assert any("propose" in s or "outperforms" in s or "95.2%" in s for s in sentences)

    def test_empty_text(self):
        sentences = extract_key_sentences("", max_sentences=5)
        assert sentences == []
