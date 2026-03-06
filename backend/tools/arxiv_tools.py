import arxiv
import logging
import os
import requests
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language (NLP)",
    "cs.CV": "Computer Vision",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.RO": "Robotics",
    "stat.ML": "Statistical Machine Learning",
}


def search_arxiv(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Search ArXiv for papers matching a query."""
    try:
        client = arxiv.Client(num_retries=3, delay_seconds=1)
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        papers = []
        for result in client.results(search):
            # Get full summary (not truncated)
            summary = result.summary.replace("\n", " ").strip()
            papers.append({
                "title": result.title,
                "summary": summary,
                "authors": [a.name for a in result.authors[:5]],
                "categories": list(result.categories),
                "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                "url": result.entry_id,
                "arxiv_id": result.entry_id.split("/")[-1],
                "pdf_url": result.pdf_url,
                "doi": result.doi,
            })
        logger.info(f"Found {len(papers)} papers for query: {query}")
        return papers
    except Exception as e:
        logger.error(f"ArXiv search error for '{query}': {e}")
        return []


def search_topic_deep(topic: str, max_results: int = 30) -> List[Dict[str, Any]]:
    """Deep search for a specific topic."""
    papers = search_arxiv(topic, max_results=max_results)
    # Also search with recent year filter
    recent_papers = search_arxiv(f"{topic} 2024 2025", max_results=15)
    seen_ids = {p["arxiv_id"] for p in papers}
    for p in recent_papers:
        if p["arxiv_id"] not in seen_ids:
            papers.append(p)
            seen_ids.add(p["arxiv_id"])
    return papers


def download_paper_pdf(arxiv_id: str, pdf_url: str, output_dir: str = "/tmp/papers") -> str:
    """Download a paper PDF and return the local path."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{arxiv_id}.pdf")

        if os.path.exists(file_path):
            return file_path

        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded PDF for {arxiv_id} to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error downloading PDF for {arxiv_id}: {e}")
        return ""


def extract_top_topics(all_papers: List[Dict[str, Any]], top_n: int = 8) -> List[Dict[str, Any]]:
    """Extract top topics from papers by clustering around categories."""
    category_groups = defaultdict(list)
    for paper in all_papers:
        primary_cat = paper["categories"][0] if paper["categories"] else "unknown"
        category_groups[primary_cat].append(paper)

    topics = []
    for cat, papers in category_groups.items():
        if len(papers) < 2:
            continue
        cat_label = CATEGORY_MAP.get(cat, cat)
        topics.append({
            "category": cat,
            "label": cat_label,
            "paper_count": len(papers),
            "papers": papers[:5],
        })
    topics.sort(key=lambda x: x["paper_count"], reverse=True)
    return topics[:top_n]


def get_paper_details(arxiv_id: str) -> Dict[str, Any]:
    """Fetch full details for a single paper by ArXiv ID."""
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        for result in client.results(search):
            return {
                "title": result.title,
                "summary": result.summary.replace("\n", " ").strip(),
                "authors": [a.name for a in result.authors],
                "categories": list(result.categories),
                "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                "url": result.entry_id,
                "arxiv_id": arxiv_id,
                "pdf_url": result.pdf_url,
            }
    except Exception as e:
        logger.error(f"Error fetching paper {arxiv_id}: {e}")
    return {}
