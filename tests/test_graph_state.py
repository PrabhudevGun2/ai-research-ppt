"""Tests for graph state definitions."""
import pytest
from backend.graph.state import (
    ResearchState, Stage, DiscoveredPaper, ProcessedPaper,
    SlideContent, GeneratedPPT, HumanFeedback, ExtractedImage,
)


class TestStage:
    def test_all_stages_defined(self):
        stages = [
            Stage.DISCOVERING_PAPERS,
            Stage.AWAITING_PAPER_SELECTION,
            Stage.PROCESSING_PAPER,
            Stage.SYNTHESIZING,
            Stage.AWAITING_SYNTHESIS_REVIEW,
            Stage.GENERATING_PPT,
            Stage.AWAITING_FINAL_REVIEW,
            Stage.COMPLETED,
            Stage.FAILED,
        ]
        assert len(stages) == 9
        assert all(isinstance(s, str) for s in stages)

    def test_stages_unique(self):
        stages = [
            Stage.DISCOVERING_PAPERS,
            Stage.AWAITING_PAPER_SELECTION,
            Stage.PROCESSING_PAPER,
            Stage.SYNTHESIZING,
            Stage.AWAITING_SYNTHESIS_REVIEW,
            Stage.GENERATING_PPT,
            Stage.AWAITING_FINAL_REVIEW,
            Stage.COMPLETED,
            Stage.FAILED,
        ]
        assert len(set(stages)) == len(stages), "All stages should be unique"


class TestTypeStructures:
    def test_discovered_paper_structure(self):
        paper: DiscoveredPaper = {
            "arxiv_id": "1234.56789",
            "title": "Test Paper",
            "authors": ["Author One"],
            "summary": "A test paper",
            "published": "2024-01-01",
            "url": "https://arxiv.org/abs/1234.56789",
            "pdf_url": "https://arxiv.org/pdf/1234.56789",
            "categories": ["cs.AI"],
        }
        assert paper["arxiv_id"] == "1234.56789"

    def test_slide_content_structure(self):
        slide: SlideContent = {
            "slide_type": "title",
            "topic": "Test",
            "title": "Test Slide",
            "subtitle": "Sub",
            "body_points": ["Point 1", "Point 2"],
            "speaker_notes": "Notes here",
            "order": 1,
            "image_path": None,
            "image_caption": None,
        }
        assert slide["order"] == 1
        assert len(slide["body_points"]) == 2
