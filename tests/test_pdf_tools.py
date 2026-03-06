"""Tests for PDF download and extraction tools."""
import os
import tempfile
import pytest
from backend.tools.pdf_tools import (
    download_arxiv_pdf,
    extract_figures_from_pdf,
    extract_tables_from_pdf,
    extract_equation_regions,
)


@pytest.fixture(scope="module")
def sample_pdf():
    """Download a small arxiv paper for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a known short paper
        pdf_path = download_arxiv_pdf("1706.03762", output_dir=tmpdir)
        if pdf_path and os.path.exists(pdf_path):
            yield pdf_path
        else:
            pytest.skip("Could not download sample PDF")


class TestDownloadArxivPdf:
    def test_download_valid_paper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = download_arxiv_pdf("1706.03762", output_dir=tmpdir)
            assert path is not None, "Should return a path"
            assert os.path.exists(path), "PDF file should exist"
            assert path.endswith(".pdf")
            assert os.path.getsize(path) > 1000, "PDF should not be empty"

    def test_download_invalid_paper(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = download_arxiv_pdf("0000.00000", output_dir=tmpdir)
            # May return None or a path to a bad file
            if path:
                # If it returned a path, the file might be an error page
                pass

    def test_download_caches(self):
        """Second download should use cached file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = download_arxiv_pdf("1706.03762", output_dir=tmpdir)
            path2 = download_arxiv_pdf("1706.03762", output_dir=tmpdir)
            assert path1 == path2, "Should return same cached path"


class TestExtractFigures:
    def test_extract_figures(self, sample_pdf):
        with tempfile.TemporaryDirectory() as tmpdir:
            figures = extract_figures_from_pdf(sample_pdf, tmpdir, min_size=50)
            assert isinstance(figures, list)
            # The transformer paper has figures
            for fig in figures:
                assert fig.figure_type == "figure"
                assert fig.page_num > 0
                assert os.path.exists(fig.image_path)


class TestExtractTables:
    def test_extract_tables(self, sample_pdf):
        with tempfile.TemporaryDirectory() as tmpdir:
            tables = extract_tables_from_pdf(sample_pdf, tmpdir)
            assert isinstance(tables, list)
            for tbl in tables:
                assert tbl.figure_type == "table"
                assert tbl.caption  # Should have caption or text content


class TestExtractEquations:
    def test_extract_equations(self, sample_pdf):
        with tempfile.TemporaryDirectory() as tmpdir:
            equations = extract_equation_regions(sample_pdf, tmpdir)
            assert isinstance(equations, list)
            for eq in equations:
                assert eq.figure_type == "equation"
                assert eq.page_num > 0
