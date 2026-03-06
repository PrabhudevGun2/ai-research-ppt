"""Tests for the paper processor agent."""
import os
import pytest
from backend.agents.paper_processor import paper_processor_node
from backend.graph.state import Stage
from backend.config import settings


class TestPaperProcessorNode:
    def test_process_paper(self):
        """Test full paper processing pipeline with a real paper."""
        state = {
            "session_id": "test-processor-1",
            "selected_paper": {
                "arxiv_id": "1706.03762",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer"],
                "summary": "The dominant sequence transduction models...",
                "published": "2017-06-12",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762",
                "categories": ["cs.CL", "cs.LG"],
            },
            "discovered_papers": [],
        }
        result = paper_processor_node(state)

        assert result["current_stage"] == Stage.SYNTHESIZING
        paper = result["processed_paper"]
        assert paper is not None
        assert paper["arxiv_id"] == "1706.03762"
        assert paper["title"] == "Attention Is All You Need"
        assert len(paper["full_text"]) > 500, "Should extract substantial text"
        assert isinstance(paper["figures"], list)
        assert isinstance(paper["tables"], list)
        assert isinstance(paper["equations"], list)

    def test_no_paper_selected(self):
        state = {
            "session_id": "test-processor-2",
            "selected_paper": None,
            "discovered_papers": [],
        }
        result = paper_processor_node(state)
        assert result["current_stage"] == Stage.FAILED

    def test_creates_output_dir(self):
        state = {
            "session_id": "test-processor-3",
            "selected_paper": {
                "arxiv_id": "1706.03762",
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani"],
                "summary": "Test",
                "published": "2017-06-12",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdf_url": "https://arxiv.org/pdf/1706.03762",
                "categories": ["cs.CL"],
            },
            "discovered_papers": [],
        }
        result = paper_processor_node(state)
        if result["current_stage"] == Stage.SYNTHESIZING:
            assets_dir = os.path.join(settings.output_dir, "test-processor-3", "assets")
            assert os.path.isdir(assets_dir)
