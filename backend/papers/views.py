import csv
import io
import json
import os
import zipfile

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.resolve_doi import resolve_doi_to_paper, fetch_sections_for_doi
from .models import ResolvedPaper, Table, Image

DATA_DIR = str(settings.SCRAPER_DATA_DIR)

_IMAGE_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


@csrf_exempt
def resolve_doi_view(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Use POST for this endpoint.",
                }
            },
            status=405,
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must be valid JSON.",
                }
            },
            status=400,
        )

    doi = (body.get("doi") or "").strip()

    if not doi:
        return JsonResponse(
            {
                "error": {
                    "code": "MISSING_DOI",
                    "message": "The 'doi' field is required.",
                }
            },
            status=400,
        )

    try:
        result = resolve_doi_to_paper(doi)

        if result.get("status") == "not_found":
            return JsonResponse(result, status=200)

        if result.get("status") == "success":
            return JsonResponse(
                {
                    "status": "success",
                    "paper": result["paper"],
                },
                status=200,
            )

        return JsonResponse(
            {
                "error": {
                    "code": "INVALID_SERVICE_RESPONSE",
                    "message": "The DOI service returned an unexpected response.",
                }
            },
            status=500,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "LOOKUP_FAILED",
                    "message": "The server could not process this DOI.",
                    "details": str(exc),
                }
            },
            status=500,
        )
    

@csrf_exempt
def fetch_sections_view(request):
    """
    POST /api/fetch-sections/
    Body: {"doi": "...", "sections": ["methods", "results"]}
    """
    if request.method != "POST":
        return JsonResponse(
            {
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": "Use POST for this endpoint.",
                }
            },
            status=405,
        )

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must be valid JSON.",
                }
            },
            status=400,
        )

    doi = (body.get("doi") or "").strip()
    sections = body.get("sections")

    if not doi:
        return JsonResponse(
            {
                "error": {
                    "code": "MISSING_DOI",
                    "message": "The 'doi' field is required.",
                }
            },
            status=400,
        )

    if not isinstance(sections, list) or not all(isinstance(s, str) and s.strip() for s in sections):
        return JsonResponse(
            {
                "error": {
                    "code": "INVALID_SECTIONS",
                    "message": "The 'sections' field must be a non-empty array of section ids.",
                }
            },
            status=400,
        )

    try:
        # Fast path: paper already in DB — read section files from disk without re-scraping.
        result = fetch_sections_for_doi(doi, sections)

        if result is None:
            # Paper not cached yet — run the full scraping pipeline, which also persists it.
            scrape = resolve_doi_to_paper(doi)
            if scrape.get("status") == "not_found":
                return JsonResponse(scrape, status=200)
            if scrape.get("status") != "success":
                return JsonResponse(
                    {"error": {"code": "SCRAPE_FAILED", "message": "The DOI could not be processed."}},
                    status=500,
                )
            result = fetch_sections_for_doi(doi, sections)

        if result is None:
            return JsonResponse(
                {"error": {"code": "INTERNAL_ERROR", "message": "Paper was saved but could not be retrieved."}},
                status=500,
            )

        return JsonResponse(result, status=200)

    except Exception as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "LOOKUP_FAILED",
                    "message": "The server could not process this DOI.",
                    "details": str(exc),
                }
            },
            status=500,
        )
    

# Source: backend/papers/models.py — ResolvedPaper
def papers_list_view(request):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    papers = ResolvedPaper.objects.all().order_by("-processed_at")
    return JsonResponse({
        "status": "success",
        "papers": [
            {
                "id": p.id,
                "doi": p.doi,
                "title": p.title,
                "source": p.source,
                "authors": p.authors,
                "num_sections": len(p.available_sections),
                "num_tables": p.tables.count(),
                "num_images": p.images.count(),
                "processed_at": p.processed_at.isoformat(),
            }
            for p in papers
        ],
    })


# Source: backend/papers/models.py — ResolvedPaper
def paper_detail_view(request, pk):
    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    if request.method == "GET":
        # Source: backend/papers/models.py — Table, Image
        tables = [
            {
                "id": t.id, "global_index": t.global_index, "table_index": t.table_index,
                "section_id": t.section.section_id, "section_name": t.section.heading,
                "csv_path": t.csv_path,
            }
            for t in paper.tables.select_related("section").all()
        ]
        images = [
            {
                "id": img.id, "idx": img.idx, "placeholder": img.placeholder,
                "caption": img.caption, "path": img.path,
                "section_id": img.section.section_id, "section_name": img.section.heading,
            }
            for img in paper.images.select_related("section").all()
        ]
        return JsonResponse({
            "status": "success",
            "paper": {
                "id": paper.id,
                "doi": paper.doi,
                "paper_id": paper.paper_id,
                "title": paper.title,
                "source": paper.source,
                "authors": paper.authors,
                "emails": paper.emails,
                "extraction_method": paper.extraction_method,
                "processed_at": paper.processed_at.isoformat(),
                "available_sections": paper.available_sections,
                "tables": tables,
                "images": images,
                "rob_artifacts": paper.rob_artifacts,
            },
        })

    if request.method == "DELETE":
        # Delete on-disk files before removing the DB rows.
        # Collect every file path stored on the paper and its children, then remove each one.
        paths_to_remove = [
            paper.md_path, paper.html_path, paper.pdf_path, paper.export_json_path,
        ]
        for sec in paper.sections.all():
            paths_to_remove.append(sec.md_path)
            for tbl in sec.tables.all():
                paths_to_remove.append(tbl.csv_path)
            for img in sec.images.all():
                paths_to_remove.append(img.path)
        for rel in paths_to_remove:
            if rel:
                try:
                    os.remove(os.path.join(DATA_DIR, rel))
                except FileNotFoundError:
                    pass

        paper.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET or DELETE."}}, status=405)


def paper_rob_view(request, pk):
    return JsonResponse(
        {"error": {"code": "NOT_IMPLEMENTED", "message": "ROB extraction is not yet implemented."}},
        status=501,
    )


# Source: backend/papers/models.py — ResolvedPaper
def paper_tables_view(request, pk):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    # Source: backend/papers/models.py — Table
    tables = [
        {
            "id": t.id, "global_index": t.global_index, "table_index": t.table_index,
            "section_id": t.section.section_id, "section_name": t.section.heading,
            "csv_path": t.csv_path,
        }
        for t in paper.tables.select_related("section").all()
    ]
    return JsonResponse({"status": "success", "tables": tables})


# Source: backend/papers/models.py — ResolvedPaper
def paper_table_detail_view(request, pk, global_index):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    # Source: backend/papers/models.py — Table
    try:
        tbl = paper.tables.select_related("section").get(global_index=global_index)
    except Table.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Table not found."}, status=404)

    if not tbl.csv_path:
        return JsonResponse({"status": "not_found", "message": "Table has no CSV file."}, status=404)

    abs_path = os.path.join(DATA_DIR, tbl.csv_path)
    try:
        with open(abs_path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        return JsonResponse({"status": "not_found", "message": "CSV file missing from disk."}, status=404)

    return JsonResponse({
        "status": "success",
        "global_index": global_index,
        "section_id": tbl.section.section_id,
        "section_name": tbl.section.heading,
        "header": rows[0] if rows else [],
        "rows": rows[1:] if len(rows) > 1 else [],
    })


# Source: backend/papers/models.py — ResolvedPaper
def paper_images_view(request, pk):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    # Source: backend/papers/models.py — Image
    images = [
        {
            "id": img.id, "idx": img.idx, "placeholder": img.placeholder,
            "caption": img.caption, "path": img.path,
            "section_id": img.section.section_id, "section_name": img.section.heading,
        }
        for img in paper.images.select_related("section").all()
    ]
    return JsonResponse({"status": "success", "images": images})


# Source: backend/papers/models.py — ResolvedPaper
def paper_image_view(request, pk, idx):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    # Source: backend/papers/models.py — Image
    try:
        img = paper.images.get(idx=idx)
    except Image.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Image not found."}, status=404)

    if not img.path:
        return JsonResponse({"status": "not_found", "message": "Image has no file path."}, status=404)

    abs_path = os.path.join(DATA_DIR, img.path)
    if not os.path.exists(abs_path):
        return JsonResponse({"status": "not_found", "message": "Image file missing from disk."}, status=404)

    ext = os.path.splitext(abs_path)[1].lower()
    content_type = _IMAGE_CONTENT_TYPES.get(ext, "image/png")
    try:
        return FileResponse(open(abs_path, "rb"), content_type=content_type)
    except OSError:
        return JsonResponse({"status": "error", "message": "Image file could not be read."}, status=500)


# ---------------------------------------------------------------------------
# Export helpers
# Source: notebooks/scraper/exporters.py — compress_directory() (in-memory variant)
# ---------------------------------------------------------------------------

def _zip_files(entries):
    """
    Build an in-memory ZIP from [(arcname, abs_path), ...].
    Missing files are silently skipped.
    Returns a BytesIO positioned at 0.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, abs_path in entries:
            if abs_path and os.path.isfile(abs_path):
                zf.write(abs_path, arcname=arcname)
    buf.seek(0)
    return buf


# Source: notebooks/scraper/exporters.py — export_documents() + notebooks/scraper/models.py — DocumentInfo.to_dict()
def _paper_to_document_dict(paper):
    """Reconstruct a DocumentInfo.to_dict()-compatible structure from DB rows."""
    sections = []
    for sec in paper.sections.prefetch_related("tables", "images").order_by("order"):
        sections.append({
            "heading": sec.heading,
            "md_path": sec.md_path,
            "tables": [
                {
                    "csv_path": t.csv_path,
                    "table_index": t.table_index,
                    "global_index": t.global_index,
                }
                for t in sec.tables.all()
            ],
            "images": [
                {
                    "placeholder": img.placeholder,
                    "caption": img.caption,
                    "path": img.path,
                }
                for img in sec.images.all()
            ],
        })

    # Mirror DocumentInfo.to_dict(): always include core fields; include optional
    # fields only when truthy so the output schema matches the scraper's JSON exports.
    res = {
        "paper_id": paper.paper_id or paper.doi,
        "source": paper.source,
        "authors": paper.authors,
        "emails": paper.emails,
    }
    # Reconstruct source-specific IDs from paper_id + source (DocumentInfo stores
    # these separately; the DB collapses them into a single paper_id column).
    if paper.source == "pmc" and paper.paper_id:
        res["pmcid"] = paper.paper_id
    elif paper.source == "arxiv" and paper.paper_id:
        res["arxiv_id"] = paper.paper_id
    if paper.extraction_method:
        res["extraction_method"] = paper.extraction_method
    if paper.md_path:
        res["md_path"] = paper.md_path
    if paper.html_path:
        res["html_path"] = paper.html_path
    if paper.pdf_path:
        res["pdf_path"] = paper.pdf_path
    res["sections"] = sections
    return res


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------

# Source: notebooks/scraper/exporters.py — compress_directory() (in-memory variant)
def paper_export_markdown_view(request, pk):
    """GET /papers/<pk>/export/markdown/ — ZIP of all section .md files."""
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    entries = []
    for sec in paper.sections.order_by("order"):
        if sec.md_path:
            arcname = f"{sec.section_id}.md"
            entries.append((arcname, os.path.join(DATA_DIR, sec.md_path)))

    if not entries:
        return JsonResponse({"status": "not_found", "message": "No markdown files found for this paper."}, status=404)

    buf = _zip_files(entries)
    safe_id = (paper.paper_id or str(paper.id)).replace("/", "_")
    response = HttpResponse(buf.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{safe_id}_markdown.zip"'
    return response


# Source: notebooks/scraper/exporters.py — compress_directory() (in-memory variant)
def paper_export_csv_view(request, pk):
    """GET /papers/<pk>/export/csv/ — ZIP of all table .csv files."""
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    entries = []
    for tbl in paper.tables.order_by("global_index"):
        if tbl.csv_path:
            arcname = f"table_{tbl.global_index}.csv"
            entries.append((arcname, os.path.join(DATA_DIR, tbl.csv_path)))

    if not entries:
        return JsonResponse({"status": "not_found", "message": "No CSV files found for this paper."}, status=404)

    buf = _zip_files(entries)
    safe_id = (paper.paper_id or str(paper.id)).replace("/", "_")
    response = HttpResponse(buf.read(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{safe_id}_tables.zip"'
    return response


# Source: notebooks/scraper/exporters.py — export_documents() + notebooks/scraper/models.py — DocumentInfo.to_dict()
def paper_export_json_view(request, pk):
    """GET /papers/<pk>/export/json/ — DocumentInfo-style JSON download."""
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    # Prefer the pre-built snapshot if it exists; otherwise reconstruct from DB.
    if paper.export_json_path:
        abs_path = os.path.join(DATA_DIR, paper.export_json_path)
        if os.path.isfile(abs_path):
            safe_id = (paper.paper_id or str(paper.id)).replace("/", "_")
            try:
                return FileResponse(
                    open(abs_path, "rb"),
                    content_type="application/json",
                    as_attachment=True,
                    filename=f"{safe_id}.json",
                )
            except OSError:
                pass  # fall through to DB reconstruction

    doc_dict = _paper_to_document_dict(paper)
    safe_id = (paper.paper_id or str(paper.id)).replace("/", "_")
    response = HttpResponse(
        json.dumps([doc_dict], ensure_ascii=False, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="{safe_id}.json"'
    return response


# Source: notebooks/scraper/exporters.py — compress_directory() (in-memory variant)
@csrf_exempt
def batch_export_view(request):
    """
    POST /batch-export/
    Body: {"paper_ids": [...], "section_types": ["method", "result"]}

    Returns a ZIP of .md and .csv files across the requested papers.
    If section_types is provided, only sections whose heading contains any of
    the supplied keywords (case-insensitive) are included, along with their tables.
    If section_types is omitted, all sections and tables are exported (original behavior).
    """
    if request.method != "POST":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use POST."}}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": {"code": "INVALID_JSON", "message": "Request body must be valid JSON."}}, status=400)

    paper_ids = body.get("paper_ids")
    if not isinstance(paper_ids, list) or not paper_ids:
        return JsonResponse({"error": {"code": "MISSING_PAPER_IDS", "message": "Provide a non-empty 'paper_ids' list."}}, status=400)

    # Source: notebooks/inspect_clean_export.ipynb — section keyword filtering
    # (df[df['heading'].str.contains(kw, case=False, na=False)])
    # Translated to Django ORM: Section.objects.filter(heading__icontains=kw)
    section_types = body.get("section_types")
    if section_types is not None:
        if not isinstance(section_types, list) or not section_types:
            return JsonResponse(
                {"error": {"code": "INVALID_SECTION_TYPES",
                           "message": "If provided, 'section_types' must be a non-empty list of strings."}},
                status=400,
            )
        if not all(isinstance(s, str) and s.strip() for s in section_types):
            return JsonResponse(
                {"error": {"code": "INVALID_SECTION_TYPES",
                           "message": "'section_types' must contain only non-empty strings."}},
                status=400,
            )
        section_types = [s.strip().lower() for s in section_types]

    papers = ResolvedPaper.objects.filter(pk__in=paper_ids)
    if not papers.exists():
        return JsonResponse({"status": "not_found", "message": "None of the requested papers were found."}, status=404)

    entries = []
    for paper in papers:
        safe_id = (paper.paper_id or str(paper.id)).replace("/", "_")

        if section_types:
            q = Q()
            for kw in section_types:
                q |= Q(heading__icontains=kw)
            sections_qs = paper.sections.filter(q).order_by("order")
        else:
            sections_qs = paper.sections.order_by("order")

        for sec in sections_qs.prefetch_related("tables"):
            if sec.md_path:
                entries.append((f"{safe_id}/sections/{sec.section_id}.md", os.path.join(DATA_DIR, sec.md_path)))
            for tbl in sec.tables.order_by("global_index"):
                if tbl.csv_path:
                    entries.append((f"{safe_id}/tables/table_{tbl.global_index}.csv", os.path.join(DATA_DIR, tbl.csv_path)))

    if not entries:
        msg = (
            "No exportable files found for the requested papers after section type filtering."
            if section_types
            else "No exportable files found for the requested papers."
        )
        return JsonResponse({"status": "not_found", "message": msg}, status=404)

    buf = _zip_files(entries)
    response = HttpResponse(buf.read(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="batch_export.zip"'
    return response


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

# Source: notebooks/to_json.py — main() batch processing loop
def _run_batch(dois):
    """
    Call resolve_doi_to_paper() for each DOI and return a unified results dict.
    Individual failures are captured per-DOI; they never abort the whole batch.
    """
    results = []
    n_success = n_not_found = n_error = 0

    for doi in dois:
        doi = doi.strip()
        if not doi:
            continue
        try:
            outcome = resolve_doi_to_paper(doi)
            status = outcome.get("status", "error")
            if status == "success":
                n_success += 1
                results.append({"doi": doi, "status": "success", "paper": outcome["paper"]})
            else:
                n_not_found += 1
                results.append({"doi": doi, "status": "not_found", "message": outcome.get("message", "")})
        except Exception as exc:
            n_error += 1
            results.append({"doi": doi, "status": "error", "message": str(exc)})

    return JsonResponse({
        "status": "success",
        "results": results,
        "summary": {
            "total": len(results),
            "success": n_success,
            "not_found": n_not_found,
            "error": n_error,
        },
    })


# Source: notebooks/to_json.py — main() batch processing loop
@csrf_exempt
def batch_process_view(request):
    """POST /batch-process/ — {"dois": [...]} → per-DOI results."""
    if request.method != "POST":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use POST."}}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": {"code": "INVALID_JSON", "message": "Request body must be valid JSON."}}, status=400)

    dois = body.get("dois")
    if not isinstance(dois, list) or not dois:
        return JsonResponse({"error": {"code": "MISSING_DOIS", "message": "Provide a non-empty 'dois' list."}}, status=400)

    return _run_batch(dois)


# Source: notebooks/to_json.py — main() DOI file reading pattern (one DOI per line)
@csrf_exempt
def batch_process_upload_view(request):
    """POST /batch-process/upload/ — multipart .txt file (one DOI per line)."""
    if request.method != "POST":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use POST."}}, status=405)

    uploaded = request.FILES.get("file")
    if not uploaded:
        return JsonResponse({"error": {"code": "MISSING_FILE", "message": "Attach a 'file' field containing a plain-text file."}}, status=400)

    try:
        text = uploaded.read().decode("utf-8")
    except Exception as exc:
        return JsonResponse({"error": {"code": "UNREADABLE_FILE", "message": f"Could not read the uploaded file: {exc}"}}, status=400)

    # Source: notebooks/to_json.py — one DOI per line, skip blanks and comments
    dois = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not dois:
        return JsonResponse({"error": {"code": "EMPTY_FILE", "message": "No DOIs found in the uploaded file."}}, status=400)

    return _run_batch(dois)


# ---------------------------------------------------------------------------
# Phase 4 — Search and ROB sub-endpoints
# ---------------------------------------------------------------------------

# Backend-specific search using Django Q objects (icontains on title and authors JSONField).
# Conceptually similar to ExportReader.search_papers() in notebooks/scraper/export_reader.py,
# but that operates on a pandas DataFrame with a configurable 'field' parameter.
def search_view(request):
    """
    GET /search/?q=<query>[&source=pmc|arxiv]

    Searches title and authors (case-insensitive).  The optional 'source'
    parameter restricts results to 'pmc' or 'arxiv'.  Returns the same shape
    as GET /papers/.
    """
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    q = request.GET.get("q", "").strip()
    source = request.GET.get("source", "").strip().lower()

    papers = ResolvedPaper.objects.all().order_by("-processed_at")

    if q:
        # authors is a JSONField; __icontains on SQLite searches the serialised text
        papers = papers.filter(Q(title__icontains=q) | Q(authors__icontains=q))

    if source in ("pmc", "arxiv"):
        papers = papers.filter(source=source)

    return JsonResponse({
        "status": "success",
        "papers": [
            {
                "id": p.id,
                "doi": p.doi,
                "title": p.title,
                "source": p.source,
                "authors": p.authors,
                "num_sections": len(p.available_sections),
                "num_tables": p.tables.count(),
                "num_images": p.images.count(),
                "processed_at": p.processed_at.isoformat(),
            }
            for p in papers
        ],
    })


def paper_rob_tables_view(request, pk):
    return JsonResponse(
        {"error": {"code": "NOT_IMPLEMENTED", "message": "ROB extraction is not yet implemented."}},
        status=501,
    )

