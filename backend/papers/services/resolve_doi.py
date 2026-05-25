"""
Service layer: resolve a DOI into a structured paper response.

Processing is delegated entirely to scraper.providers.process_document()
(source: notebooks/scraper/providers.py) which returns a DocumentInfo object
whose sections already have their markdown files saved to disk.

ROB extraction is handled by the existing rob_extraction module.
"""
import os
import re

from django.conf import settings

# Source: notebooks/scraper/providers.py — process_document()
from scraper.providers import process_document

# Source: notebooks/scraper/parsers_md.py — parse_markdown(), normalize()
from scraper.parsers_md import parse_markdown, normalize

from .rob_extraction import extract_rob_artifacts_from_markdown

DATA_DIR = str(settings.SCRAPER_DATA_DIR)


# Source: notebooks/to_json.py / resolve_doi_sections.py — make_section_id()
def _make_section_id(name: str) -> str:
    return normalize(name).lower().replace(" ", "_")


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def resolve_doi_to_paper(doi: str) -> dict:
    doi = normalize(doi)

    if not doi:
        return {"status": "not_found", "message": "No DOI was provided."}

    # Source: notebooks/scraper/providers.py — process_document()
    # Runs the full pipeline: fetch → parse → split sections → save CSVs/images.
    doc = process_document(doi, base_dir=DATA_DIR)

    if not doc:
        return {"status": "not_found", "message": "We couldn't find a paper for this DOI."}

    # Resolve the full-document markdown path (relative stored in doc.md_path)
    md_full_path = os.path.join(DATA_DIR, doc.md_path) if doc.md_path else None
    if not md_full_path or not os.path.exists(md_full_path):
        return {
            "status": "not_found",
            "message": "The paper was found, but no markdown file was produced.",
        }

    md_text = _load_text(md_full_path)

    # Source: notebooks/scraper/parsers_md.py — parse_markdown()
    # Extract the title from the H1 heading of the full document.
    title, _ = parse_markdown(md_text)

    # Source: backend/papers/services/rob_extraction.py
    # Scan the full markdown for ROB tables and section keywords.
    rob_artifacts = extract_rob_artifacts_from_markdown(md_text, paper_id=doi)

    # Source: notebooks/scraper/providers.py — process_sections_and_tables()
    # doc.sections is already populated: each SectionInfo has heading + md_path
    # (relative to DATA_DIR) pointing to the per-section markdown file on disk.
    available_sections = []
    section_map = {}

    for section in doc.sections:
        name = section.heading
        if not name:
            continue

        section_id = _make_section_id(name)
        available_sections.append({"id": section_id, "name": name})

        # Load the section's markdown file written by process_sections_and_tables()
        if section.md_path:
            sec_full_path = os.path.join(DATA_DIR, section.md_path)
            try:
                section_map[section_id] = _load_text(sec_full_path)
            except FileNotFoundError:
                section_map[section_id] = ""
        else:
            section_map[section_id] = ""

    return {
        "status": "success",
        "paper": {
            "doi": doi,
            "title": title or "Untitled paper",
            "source": doc.source,
            "authors": doc.authors,
            "emails": doc.emails,
            "robArtifacts": rob_artifacts,
            "availableSections": available_sections,
        },
        "section_map": section_map,
    }
