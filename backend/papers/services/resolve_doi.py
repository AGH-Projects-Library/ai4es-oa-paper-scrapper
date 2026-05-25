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
from scraper.providers import process_document
from scraper.parsers_md import parse_markdown, normalize
from .rob_extraction import extract_rob_artifacts_from_markdown
from papers.models import ResolvedPaper, Section

DATA_DIR = str(settings.SCRAPER_DATA_DIR)


# Source: notebooks/to_json.py / resolve_doi_sections.py — make_section_id()
def _make_section_id(name: str) -> str:
    return normalize(name).lower().replace(" ", "_")


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Source: backend/papers/models.py — ResolvedPaper, Section
def _save_to_db(doi, doc, title, rob_artifacts):
    available_sections = [
        {"id": _make_section_id(s.heading), "name": s.heading}
        for s in doc.sections if s.heading
    ]

    tables_metadata = []
    images_metadata = []
    img_idx = 0
    for s in doc.sections:
        if not s.heading:
            continue
        sid = _make_section_id(s.heading)
        for tbl in (s.tables or []):
            tables_metadata.append({
                "global_index": tbl.global_index,
                "section_id": sid,
                "section_name": s.heading,
                "table_index": tbl.table_index,
                "csv_path": tbl.csv_path or "",
            })
        for img in (s.images or []):
            images_metadata.append({
                "idx": img_idx,
                "section_id": sid,
                "section_name": s.heading,
                "placeholder": img.placeholder,
                "caption": img.caption,
                "path": img.path or "",
            })
            img_idx += 1

    paper, _ = ResolvedPaper.objects.update_or_create(
        doi=doi,
        defaults={
            "paper_id": getattr(doc, "paper_id", "") or "",
            "title": title or "Untitled paper",
            "source": doc.source,
            "authors": doc.authors,
            "emails": doc.emails,
            "extraction_method": getattr(doc, "extraction_method", "") or "",
            "md_path": doc.md_path or "",
            "html_path": getattr(doc, "html_path", "") or "",
            "pdf_path": getattr(doc, "pdf_path", "") or "",
            "rob_artifacts": rob_artifacts,
            "available_sections": available_sections,
            "tables_metadata": tables_metadata,
            "images_metadata": images_metadata,
        },
    )
    paper.sections.all().delete()
    Section.objects.bulk_create([
        Section(
            paper=paper,
            section_id=_make_section_id(s.heading),
            heading=s.heading,
            order=i,
            md_path=s.md_path or "",
        )
        for i, s in enumerate(doc.sections) if s.heading
    ])


# Source: backend/papers/models.py — ResolvedPaper
def _load_from_db(doi) -> dict | None:
    try:
        paper = ResolvedPaper.objects.get(doi=doi)
    except ResolvedPaper.DoesNotExist:
        return None
    return {
        "status": "success",
        "paper": {
            "doi": doi,
            "title": paper.title,
            "source": paper.source,
            "authors": paper.authors,
            "emails": paper.emails,
            "robArtifacts": paper.rob_artifacts,
            "availableSections": paper.available_sections,
        },
    }


# Source: backend/papers/models.py — ResolvedPaper, Section
def fetch_sections_for_doi(doi: str, requested_ids: list) -> dict | None:
    try:
        paper = ResolvedPaper.objects.get(doi=doi)
    except ResolvedPaper.DoesNotExist:
        return None

    avail = {s["id"]: s["name"] for s in paper.available_sections}
    db_sections = {s.section_id: s for s in paper.sections.all()}

    out = []
    for sec_id in requested_ids:
        sec_id = sec_id.strip()
        if sec_id not in avail:
            continue
        db_sec = db_sections.get(sec_id)
        content = ""
        if db_sec and db_sec.md_path:
            try:
                content = _load_text(os.path.join(DATA_DIR, db_sec.md_path))
            except FileNotFoundError:
                pass
        out.append({"id": sec_id, "name": avail[sec_id], "content": content})

    return {"status": "success", "sections": out}


def resolve_doi_to_paper(doi: str) -> dict:
    doi = normalize(doi)

    if not doi:
        return {"status": "not_found", "message": "No DOI was provided."}

    # Fast path: return cached result from DB
    cached = _load_from_db(doi)
    if cached:
        return cached

    # Source: notebooks/scraper/providers.py — process_document()
    # Slow path: run the full scraping pipeline (fetch → parse → split sections → save files).
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
    title, _ = parse_markdown(md_text)

    # Source: backend/papers/services/rob_extraction.py
    rob_artifacts = extract_rob_artifacts_from_markdown(md_text, paper_id=doi)

    # Persist to DB before returning
    _save_to_db(doi, doc, title, rob_artifacts)

    return {
        "status": "success",
        "paper": {
            "doi": doi,
            "title": title or "Untitled paper",
            "source": doc.source,
            "authors": doc.authors,
            "emails": doc.emails,
            "robArtifacts": rob_artifacts,
            "availableSections": [
                {"id": _make_section_id(s.heading), "name": s.heading}
                for s in doc.sections if s.heading
            ],
        },
    }
