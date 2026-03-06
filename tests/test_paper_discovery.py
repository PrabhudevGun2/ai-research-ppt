"""Tests for the paper discovery agent."""
import pytest
from backend.agents.paper_discovery import paper_discovery_node, extract_arxiv_id_from_url
from backend.graph.state import Stage


class TestExtractArxivId:
    def test_abs_url(self):
        assert extract_arxiv_id_from_url("https://arxiv.org/abs/2401.12345") == "2401.12345"

    def test_pdf_url(self):
        assert extract_arxiv_id_from_url("https://arxiv.org/pdf/2401.12345") == "2401.12345"

    def test_bare_id(self):
        assert extract_arxiv_id_from_url("2401.12345") == "2401.12345"

    def test_five_digit(self):
        assert extract_arxiv_id_from_url("https://arxiv.org/abs/2401.12345") == "2401.12345"

    def test_invalid_url(self):
        result = extract_arxiv_id_from_url("https://google.com")
        assert result is None

    def test_no_url(self):
        result = extract_arxiv_id_from_url("not a url at all")
        assert result is None


class TestPaperDiscoveryNode:
    def test_topic_search_mode(self):
        state = {
            "session_id": "test-discovery-1",
            "user_query": "transformer attention mechanism",
            "arxiv_url": None,
            "is_single_paper_mode": False,
            "discovered_papers": [],
            "selected_paper": None,
        }
        result = paper_discovery_node(state)
        assert result["current_stage"] == Stage.AWAITING_PAPER_SELECTION
        assert len(result["discovered_papers"]) > 0

        paper = result["discovered_papers"][0]
        assert "title" in paper
        assert "arxiv_id" in paper

    def test_single_paper_mode(self):
        state = {
            "session_id": "test-discovery-2",
            "user_query": "",
            "arxiv_url": "https://arxiv.org/abs/1706.03762",
            "is_single_paper_mode": True,
            "discovered_papers": [],
            "selected_paper": None,
        }
        result = paper_discovery_node(state)
        assert result["current_stage"] == Stage.PROCESSING_PAPER
        assert len(result["discovered_papers"]) == 1
        assert result["selected_paper"] is not None
        assert "attention" in result["selected_paper"]["title"].lower() or "transformer" in result["selected_paper"]["title"].lower()

    def test_invalid_arxiv_url(self):
        state = {
            "session_id": "test-discovery-3",
            "user_query": "",
            "arxiv_url": "https://google.com/not-arxiv",
            "is_single_paper_mode": True,
            "discovered_papers": [],
            "selected_paper": None,
        }
        result = paper_discovery_node(state)
        assert result["current_stage"] == Stage.FAILED
        assert len(result.get("errors", [])) > 0
