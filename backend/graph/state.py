from typing import TypedDict, List, Optional, Annotated
import operator


class DiscoveredPaper(TypedDict):
    """A paper discovered from ArXiv search."""
    arxiv_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    url: str
    pdf_url: str
    categories: List[str]


class ExtractedImage(TypedDict):
    """An extracted figure/table from paper PDF."""
    figure_type: str  # "figure", "table", "equation"
    page_num: int
    image_path: str
    caption: str
    text_content: str


class ProcessedPaper(TypedDict):
    """A fully processed paper with extracted content."""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    full_text: str
    sections: dict  # section_name -> text
    figures: List[ExtractedImage]
    tables: List[ExtractedImage]
    equations: List[ExtractedImage]


class SlideContent(TypedDict):
    slide_type: str  # title, problem, background, contribution, methodology, architecture, equation, algorithm, experiments, results, analysis, limitations, practical, future, summary, references
    topic: Optional[str]
    title: str
    subtitle: Optional[str]
    body_points: List[str]
    speaker_notes: Optional[str]
    order: int
    image_path: Optional[str]  # Path to figure/table image if applicable
    image_caption: Optional[str]


class GeneratedPPT(TypedDict):
    file_path: str
    doc_path: Optional[str]
    pdf_path: Optional[str]
    session_id: str
    slide_count: int
    topics_covered: List[str]
    generated_at: str


class HumanFeedback(TypedDict):
    stage: str
    action: str
    feedback_text: Optional[str]
    modified_data: Optional[dict]
    timestamp: str


class ResearchState(TypedDict):
    session_id: str
    user_query: str
    current_stage: str
    audience: str  # "executive", "fresher", "engineer", "researcher"
    # Mode flag
    is_single_paper_mode: bool  # True if user provided arxiv link directly
    arxiv_url: Optional[str]  # Direct arxiv URL if provided
    # For topic search mode
    discovered_papers: List[DiscoveredPaper]
    selected_paper: Optional[DiscoveredPaper]
    # Processed paper content
    processed_paper: Optional[ProcessedPaper]
    # Slide content
    slide_contents: List[SlideContent]
    approved_slides: List[SlideContent]
    # Output
    generated_ppt: Optional[GeneratedPPT]
    human_feedback_history: Annotated[List[HumanFeedback], operator.add]
    errors: Annotated[List[str], operator.add]


class Stage:
    DISCOVERING_PAPERS = "discovering_papers"
    AWAITING_PAPER_SELECTION = "awaiting_paper_selection"
    PROCESSING_PAPER = "processing_paper"
    SYNTHESIZING = "synthesizing"
    AWAITING_SYNTHESIS_REVIEW = "awaiting_synthesis_review"
    GENERATING_PPT = "generating_ppt"
    AWAITING_FINAL_REVIEW = "awaiting_final_review"
    COMPLETED = "completed"
    FAILED = "failed"