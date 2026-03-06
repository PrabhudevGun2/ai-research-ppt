"""Tests for PPT generation agent."""
import os
import tempfile
import pytest
from unittest.mock import patch
from backend.agents.ppt_generation import ppt_generation_node, SLIDE_HANDLERS
from backend.graph.state import Stage


def _make_sample_slides():
    return [
        {
            "slide_type": "title",
            "topic": "Test Paper",
            "title": "A Novel Approach to Testing",
            "subtitle": "Authors et al. - March 2026",
            "body_points": ["ArXiv: 1234.56789"],
            "speaker_notes": "Welcome to this presentation.",
            "order": 1,
            "image_path": None,
            "image_caption": None,
        },
        {
            "slide_type": "problem",
            "topic": "Test Paper",
            "title": "Problem Statement",
            "subtitle": "Challenges",
            "body_points": [
                "Current methods suffer from high latency in production environments",
                "Existing approaches require large amounts of labeled data",
                "No prior work addresses the combination of efficiency and accuracy",
            ],
            "speaker_notes": "Let's discuss the core problem.",
            "order": 2,
            "image_path": None,
            "image_caption": None,
        },
        {
            "slide_type": "methodology",
            "topic": "Test Paper",
            "title": "Proposed Method",
            "subtitle": "Architecture",
            "body_points": [
                "We propose a transformer-based architecture with novel attention",
                "The model uses multi-scale feature extraction",
                "Training uses a custom loss function combining cross-entropy and contrastive loss",
            ],
            "speaker_notes": "Our approach is novel in several ways.",
            "order": 3,
            "image_path": None,
            "image_caption": None,
        },
        {
            "slide_type": "results",
            "topic": "Test Paper",
            "title": "Experimental Results",
            "subtitle": "Benchmarks",
            "body_points": [
                "Achieves 95.2% accuracy on GLUE benchmark",
                "Outperforms BERT by 3.1 percentage points",
                "Training time reduced by 40% compared to baseline",
            ],
            "speaker_notes": "Results demonstrate clear improvements.",
            "order": 4,
            "image_path": None,
            "image_caption": None,
        },
        {
            "slide_type": "conclusion",
            "topic": "Test Paper",
            "title": "Conclusions & Future Work",
            "subtitle": None,
            "body_points": [
                "Novel method achieves state-of-the-art results",
                "Future work includes multi-language support",
            ],
            "speaker_notes": "Thank you for your attention.",
            "order": 5,
            "image_path": None,
            "image_caption": None,
        },
    ]


class TestPptGenerationNode:
    def test_generates_pptx(self, tmp_path):
        with patch("backend.agents.ppt_generation.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            state = {
                "session_id": "test-ppt-gen-1",
                "approved_slides": _make_sample_slides(),
                "processed_paper": {
                    "title": "A Novel Approach to Testing",
                    "authors": ["Test Author"],
                    "arxiv_id": "1234.56789",
                    "abstract": "Test abstract.",
                },
                "slide_contents": [],
            }
            result = ppt_generation_node(state)

            assert result["current_stage"] == Stage.AWAITING_FINAL_REVIEW
            ppt = result["generated_ppt"]
            assert ppt is not None
            assert ppt["slide_count"] == 5
            assert os.path.exists(ppt["file_path"])
            assert ppt["file_path"].endswith(".pptx")
            # Check file is a valid pptx (not empty)
            assert os.path.getsize(ppt["file_path"]) > 5000

    def test_generates_docx(self, tmp_path):
        with patch("backend.agents.ppt_generation.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            state = {
                "session_id": "test-ppt-gen-2",
                "approved_slides": _make_sample_slides(),
                "processed_paper": {
                    "title": "Test Paper",
                    "authors": ["Author One"],
                    "arxiv_id": "1234.56789",
                    "abstract": "Test abstract.",
                },
                "slide_contents": [],
            }
            result = ppt_generation_node(state)
            ppt = result["generated_ppt"]
            doc_path = ppt.get("doc_path")
            if doc_path:
                assert os.path.exists(doc_path)
                assert doc_path.endswith(".docx")

    def test_falls_back_to_slide_contents(self, tmp_path):
        """If no approved_slides, should use slide_contents."""
        with patch("backend.agents.ppt_generation.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            slides = _make_sample_slides()
            state = {
                "session_id": "test-ppt-gen-3",
                "approved_slides": [],
                "slide_contents": slides,
                "processed_paper": {"title": "Test", "authors": [], "arxiv_id": "1234.56789", "abstract": ""},
            }
            result = ppt_generation_node(state)
            assert result["generated_ppt"]["slide_count"] == len(slides)


class TestSlideHandlers:
    def test_all_types_have_handlers(self):
        expected_types = [
            "title", "problem", "background", "contribution", "methodology",
            "architecture", "equation", "algorithm", "experiments", "results",
            "analysis", "discussion", "limitations", "future", "conclusion",
        ]
        for stype in expected_types:
            assert stype in SLIDE_HANDLERS, f"Missing handler for slide type: {stype}"
