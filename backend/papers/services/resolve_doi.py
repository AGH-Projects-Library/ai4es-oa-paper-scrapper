"""
Service layer: resolve a DOI into a structured paper response.

Processing is delegated entirely to scraper.providers.process_document()
(source: notebooks/scraper/providers.py) which returns a DocumentInfo object
whose sections already have their markdown files saved to disk.

ROB extraction is handled by the existing rob_extraction module.
"""
import os

from django.conf import settings
from scraper.providers import process_document
from scraper.parsers_md import parse_markdown, normalize
from scraper.exporters import export_documents as scraper_export_documents
from papers.models import ResolvedPaper, Section, Table, Image

DATA_DIR = str(settings.SCRAPER_DATA_DIR)


# Mirrors make_section_id() from the now-removed resolve_doi_sections.py.
# This inline copy is the authoritative version.
def _make_section_id(name: str) -> str:
    return normalize(name).lower().replace(" ", "_")


def _load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Source: backend/papers/models.py — ResolvedPaper, Section, Table, Image
def _save_to_db(doi, doc, title, rob_artifacts=None):
    available_sections = [
        {"id": _make_section_id(s.heading), "name": s.heading}
        for s in doc.sections if s.heading
    ]

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
            "rob_artifacts": rob_artifacts or [],
            "available_sections": available_sections,
        },
    )

    # Deleting sections cascades to Table and Image rows.
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

    # Re-fetch sections so we have their PKs for the FK relations below.
    section_map = {s.section_id: s for s in paper.sections.all()}

    table_rows = []
    image_rows = []
    img_idx = 0
    for s in doc.sections:
        if not s.heading:
            continue
        db_sec = section_map.get(_make_section_id(s.heading))
        if db_sec is None:
            continue
        for tbl in (s.tables or []):
            table_rows.append(Table(
                paper=paper,
                section=db_sec,
                table_index=tbl.table_index,
                global_index=tbl.global_index,
                csv_path=tbl.csv_path or "",
            ))
        for img in (s.images or []):
            image_rows.append(Image(
                paper=paper,
                section=db_sec,
                idx=img_idx,
                placeholder=img.placeholder,
                caption=img.caption,
                path=img.path or "",
            ))
            img_idx += 1

    Table.objects.bulk_create(table_rows)
    Image.objects.bulk_create(image_rows)

    # Source: notebooks/scraper/exporters.py — export_documents()
    # Write a DocumentInfo JSON snapshot so the paper can be loaded by ExportReader later.
    try:
        export_dir = os.path.join(DATA_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        safe_id = (paper.paper_id or doi).replace("/", "_").replace(":", "_")
        export_abs = os.path.join(export_dir, f"{safe_id}.json")
        scraper_export_documents([doc], export_abs)
        paper.export_json_path = os.path.relpath(export_abs, DATA_DIR)
        paper.save(update_fields=["export_json_path"])
    except Exception:
        pass  # export snapshot is best-effort; don't fail the whole scrape

    return paper


# Source: backend/papers/models.py — ResolvedPaper
def _load_from_db(doi) -> dict | None:
    try:
        paper = ResolvedPaper.objects.get(doi=doi)
    except ResolvedPaper.DoesNotExist:
        return None
    return {
        "status": "success",
        "paper": {
            "id": paper.id,
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

    # Persist to DB before returning
    saved_paper = _save_to_db(doi, doc, title, rob_artifacts=[])

    return {
        "status": "success",
        "paper": {
            "id": saved_paper.id,
            "doi": doi,
            "title": title or "Untitled paper",
            "source": doc.source,
            "authors": doc.authors,
            "emails": doc.emails,
            "robArtifacts": [],
            "availableSections": [
                {"id": _make_section_id(s.heading), "name": s.heading}
                for s in doc.sections if s.heading
            ],
        },
    }
