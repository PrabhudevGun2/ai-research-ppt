"""Tests for the slide synthesis agent (uses LLM - fast model)."""
import json
import pytest
from backend.agents.slide_synthesis import slide_synthesis_node, _fallback_slides, _find_matching_asset
from backend.graph.state import Stage


def _make_processed_paper():
    return {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "full_text": "This is the full text of the paper about transformers and attention mechanisms...",
        "sections": {
            "introduction": "The introduction discusses the limitations of RNNs and CNNs...",
            "method": "We propose the Transformer architecture based on self-attention...",
            "results": "Our model achieves 28.4 BLEU on English-to-German translation...",
        },
        "figures": [
            {"caption": "Figure 1: The Transformer model architecture", "image_path": "/tmp/fake.png"},
        ],
        "tables": [
            {"caption": "Table 1: Translation quality comparison", "image_path": "/tmp/fake_table.png"},
        ],
        "equations": [],
    }


class TestSlideSynthesisNode:
    def test_generates_slides(self):
        """Test that LLM generates valid slide content."""
        state = {
            "session_id": "test-synthesis-1",
            "processed_paper": _make_processed_paper(),
        }
        result = slide_synthesis_node(state)

        assert result["current_stage"] == Stage.AWAITING_SYNTHESIS_REVIEW
        slides = result["slide_contents"]
        assert len(slides) >= 5, f"Should generate at least 5 slides, got {len(slides)}"

        for slide in slides:
            assert "title" in slide, "Each slide must have a title"
            assert "body_points" in slide, "Each slide must have body_points"
            assert "slide_type" in slide, "Each slide must have a slide_type"
            assert "order" in slide, "Each slide must have an order"
            assert isinstance(slide["body_points"], list)

    def test_no_paper_fails(self):
        state = {
            "session_id": "test-synthesis-2",
            "processed_paper": None,
        }
        result = slide_synthesis_node(state)
        assert result["current_stage"] == Stage.FAILED

    def test_slide_types_valid(self):
        state = {
            "session_id": "test-synthesis-3",
            "processed_paper": _make_processed_paper(),
        }
        result = slide_synthesis_node(state)
        valid_types = {
            "title", "problem", "background", "contribution", "methodology",
            "method", "architecture", "equation", "equations", "algorithm",
            "experiments", "results", "evaluation", "analysis", "discussion",
            "limitations", "future", "conclusion", "references", "content",
            "summary", "practical",
        }
        for slide in result.get("slide_contents", []):
            assert slide["slide_type"] in valid_types, f"Invalid slide_type: {slide['slide_type']}"


class TestFallbackSlides:
    def test_fallback_creates_slides(self):
        paper = _make_processed_paper()
        slides = _fallback_slides(paper)
        assert len(slides) >= 3
        assert slides[0]["slide_type"] == "title"
        assert slides[0]["title"] == paper["title"]


class TestFindMatchingAsset:
    def test_matches_figure(self):
        figures = [{"image_path": "/tmp/fig1.png", "caption": "Figure 1 caption"}]
        tables = []
        path, caption = _find_matching_asset("Figure 1", figures, tables)
        assert path == "/tmp/fig1.png"

    def test_matches_table(self):
        figures = []
        tables = [{"image_path": "/tmp/tbl1.png", "caption": "Table 1 results"}]
        path, caption = _find_matching_asset("Table 1", figures, tables)
        assert path == "/tmp/tbl1.png"

    def test_no_match(self):
        path, caption = _find_matching_asset("Figure 99", [], [])
        assert path is None
        assert caption is None

    def test_invalid_recommendation(self):
        path, caption = _find_matching_asset("something weird", [], [])
        assert path is None
