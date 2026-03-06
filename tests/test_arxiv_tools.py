"""Tests for ArXiv search and paper fetching tools."""
import pytest
from backend.tools.arxiv_tools import (
    search_arxiv,
    get_paper_details,
    extract_top_topics,
    download_paper_pdf,
)


class TestSearchArxiv:
    def test_search_returns_results(self):
        papers = search_arxiv("attention is all you need transformer", max_results=3)
        assert len(papers) > 0, "Should return at least one paper"

    def test_search_paper_structure(self):
        papers = search_arxiv("BERT language model", max_results=2)
        assert len(papers) > 0
        paper = papers[0]
        required_keys = ["title", "summary", "authors", "categories", "published", "url", "arxiv_id", "pdf_url"]
        for key in required_keys:
            assert key in paper, f"Paper missing key: {key}"

    def test_search_empty_query(self):
        papers = search_arxiv("", max_results=1)
        # Should not crash, may return empty or some results
        assert isinstance(papers, list)

    def test_search_respects_max_results(self):
        papers = search_arxiv("deep learning", max_results=5)
        assert len(papers) <= 5


class TestGetPaperDetails:
    def test_valid_paper_id(self):
        # "Attention Is All You Need"
        paper = get_paper_details("1706.03762")
        assert paper, "Should return paper details"
        assert "title" in paper
        assert "transformer" in paper["title"].lower() or "attention" in paper["title"].lower()

    def test_invalid_paper_id(self):
        paper = get_paper_details("9999.99999")
        assert paper == {} or paper is None, "Invalid ID should return empty"


class TestExtractTopTopics:
    def test_extracts_topics(self):
        fake_papers = [
            {"categories": ["cs.AI"], "title": f"Paper {i}"} for i in range(5)
        ] + [
            {"categories": ["cs.CL"], "title": f"NLP Paper {i}"} for i in range(3)
        ]
        topics = extract_top_topics(fake_papers, top_n=5)
        assert len(topics) >= 1
        assert topics[0]["paper_count"] >= 2

    def test_empty_papers(self):
        topics = extract_top_topics([], top_n=5)
        assert topics == []
