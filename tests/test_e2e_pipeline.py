"""End-to-end pipeline test: discovery -> processing -> synthesis -> PPT generation.

Runs the full pipeline WITHOUT Redis/LangGraph checkpointing by calling
each agent node directly in sequence. Uses the fast model for LLM calls.
"""
import os
import tempfile
import pytest
from unittest.mock import patch

from backend.agents.paper_discovery import paper_discovery_node
from backend.agents.paper_processor import paper_processor_node
from backend.agents.slide_synthesis import slide_synthesis_node
from backend.agents.ppt_generation import ppt_generation_node
from backend.graph.state import Stage


@pytest.mark.slow
class TestEndToEndPipeline:
    """Full pipeline test with a real arxiv paper and fast LLM."""

    def test_full_pipeline_single_paper(self, tmp_path):
        """Test: arxiv URL -> PDF download -> text extraction -> slide synthesis -> PPT."""
        session_id = "e2e-test-1"

        # Step 1: Paper Discovery (single paper mode)
        discovery_state = {
            "session_id": session_id,
            "user_query": "",
            "arxiv_url": "https://arxiv.org/abs/1706.03762",
            "is_single_paper_mode": True,
            "discovered_papers": [],
            "selected_paper": None,
        }
        discovery_result = paper_discovery_node(discovery_state)
        assert discovery_result["current_stage"] == Stage.PROCESSING_PAPER, (
            f"Discovery failed: {discovery_result}"
        )
        assert discovery_result["selected_paper"] is not None
        print(f"  Discovery OK: {discovery_result['selected_paper']['title']}")

        # Step 2: Paper Processing
        with patch("backend.agents.paper_processor.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            processor_state = {
                "session_id": session_id,
                "selected_paper": discovery_result["selected_paper"],
                "discovered_papers": discovery_result["discovered_papers"],
            }
            processor_result = paper_processor_node(processor_state)

        assert processor_result["current_stage"] == Stage.SYNTHESIZING, (
            f"Processing failed: {processor_result}"
        )
        paper = processor_result["processed_paper"]
        assert paper is not None
        assert len(paper["full_text"]) > 500
        print(f"  Processing OK: {len(paper['full_text'])} chars, "
              f"{len(paper['figures'])} figures, {len(paper['tables'])} tables")

        # Step 3: Slide Synthesis (LLM call - uses fast model)
        synthesis_state = {
            "session_id": session_id,
            "processed_paper": processor_result["processed_paper"],
        }
        synthesis_result = slide_synthesis_node(synthesis_state)
        assert synthesis_result["current_stage"] == Stage.AWAITING_SYNTHESIS_REVIEW, (
            f"Synthesis failed: {synthesis_result}"
        )
        slides = synthesis_result["slide_contents"]
        assert len(slides) >= 5, f"Expected 5+ slides, got {len(slides)}"
        print(f"  Synthesis OK: {len(slides)} slides generated")

        # Validate slide quality
        for slide in slides:
            assert slide.get("title"), f"Slide missing title: {slide}"
            assert slide.get("body_points"), f"Slide missing body_points: {slide}"

        # Step 4: PPT Generation
        with patch("backend.agents.ppt_generation.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            ppt_state = {
                "session_id": session_id,
                "approved_slides": slides,
                "slide_contents": slides,
                "processed_paper": processor_result["processed_paper"],
                "selected_paper": discovery_result["selected_paper"],
            }
            ppt_result = ppt_generation_node(ppt_state)

        assert ppt_result["current_stage"] == Stage.AWAITING_FINAL_REVIEW
        generated_ppt = ppt_result["generated_ppt"]
        assert generated_ppt is not None
        assert os.path.exists(generated_ppt["file_path"])
        pptx_size = os.path.getsize(generated_ppt["file_path"])
        assert pptx_size > 10000, f"PPTX too small: {pptx_size} bytes"
        print(f"  PPT Generation OK: {generated_ppt['slide_count']} slides, {pptx_size} bytes")

        # Check DOCX was also generated
        doc_path = generated_ppt.get("doc_path")
        if doc_path and os.path.exists(doc_path):
            docx_size = os.path.getsize(doc_path)
            print(f"  DOCX also generated: {docx_size} bytes")

        print(f"\n  FULL PIPELINE PASSED for 'Attention Is All You Need'")

    def test_full_pipeline_topic_search(self, tmp_path):
        """Test: topic search -> pick first paper -> process -> synthesize -> PPT."""
        session_id = "e2e-test-2"

        # Step 1: Topic search
        discovery_state = {
            "session_id": session_id,
            "user_query": "vision transformer ViT image classification",
            "arxiv_url": None,
            "is_single_paper_mode": False,
            "discovered_papers": [],
            "selected_paper": None,
        }
        discovery_result = paper_discovery_node(discovery_state)
        assert discovery_result["current_stage"] == Stage.AWAITING_PAPER_SELECTION
        papers = discovery_result["discovered_papers"]
        assert len(papers) > 0, "Should find papers about ViT"
        print(f"  Discovery OK: Found {len(papers)} papers")

        # Simulate human selecting first paper
        selected = papers[0]
        print(f"  Selected: {selected['title']}")

        # Step 2: Process
        with patch("backend.agents.paper_processor.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            processor_state = {
                "session_id": session_id,
                "selected_paper": selected,
                "discovered_papers": papers,
            }
            processor_result = paper_processor_node(processor_state)

        assert processor_result["current_stage"] == Stage.SYNTHESIZING
        print(f"  Processing OK: {len(processor_result['processed_paper']['full_text'])} chars")

        # Step 3: Synthesize
        synthesis_state = {
            "session_id": session_id,
            "processed_paper": processor_result["processed_paper"],
        }
        synthesis_result = slide_synthesis_node(synthesis_state)
        assert synthesis_result["current_stage"] == Stage.AWAITING_SYNTHESIS_REVIEW
        slides = synthesis_result["slide_contents"]
        assert len(slides) >= 5
        print(f"  Synthesis OK: {len(slides)} slides")

        # Step 4: Generate PPT
        with patch("backend.agents.ppt_generation.settings") as mock_settings:
            mock_settings.output_dir = str(tmp_path)
            ppt_state = {
                "session_id": session_id,
                "approved_slides": slides,
                "slide_contents": slides,
                "processed_paper": processor_result["processed_paper"],
                "selected_paper": selected,
            }
            ppt_result = ppt_generation_node(ppt_state)

        assert ppt_result["current_stage"] == Stage.AWAITING_FINAL_REVIEW
        assert os.path.exists(ppt_result["generated_ppt"]["file_path"])
        print(f"  PPT OK: {ppt_result['generated_ppt']['slide_count']} slides")
        print(f"\n  FULL PIPELINE PASSED for topic search")
