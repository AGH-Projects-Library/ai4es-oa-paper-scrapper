import csv
import json
import os

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services.resolve_doi import resolve_doi_to_paper, fetch_sections_for_doi
from .models import ResolvedPaper

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
            if scrape.get("status") != "success":
                return JsonResponse(scrape, status=200)
            result = fetch_sections_for_doi(doi, sections)

        if result is None:
            return JsonResponse(
                {"status": "not_found", "message": "We couldn't find a paper for this DOI."},
                status=200,
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
    
def get_section_content_view(request, section_id):
    return JsonResponse(
        {
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "This endpoint was replaced by POST /api/fetch-sections/.",
            }
        },
        status=405,
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
                "num_tables": len(p.tables_metadata),
                "num_images": len(p.images_metadata),
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
                "tables_metadata": paper.tables_metadata,
                "images_metadata": paper.images_metadata,
                "rob_artifacts": paper.rob_artifacts,
            },
        })

    if request.method == "DELETE":
        paper.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET or DELETE."}}, status=405)


# Source: backend/papers/models.py — ResolvedPaper
def paper_rob_view(request, pk):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    return JsonResponse({"status": "success", "rob_artifacts": paper.rob_artifacts})


# Source: backend/papers/models.py — ResolvedPaper
def paper_tables_view(request, pk):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    return JsonResponse({"status": "success", "tables": paper.tables_metadata})


# Source: backend/papers/models.py — ResolvedPaper
# Source: backend/scraper/parsers_md.py — parse_md_table() pattern (CSV variant)
def paper_table_detail_view(request, pk, global_index):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    entry = next((t for t in paper.tables_metadata if t.get("global_index") == global_index), None)
    if not entry or not entry.get("csv_path"):
        return JsonResponse({"status": "not_found", "message": "Table not found."}, status=404)

    abs_path = os.path.join(DATA_DIR, entry["csv_path"])
    try:
        with open(abs_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except FileNotFoundError:
        return JsonResponse({"status": "not_found", "message": "CSV file missing from disk."}, status=404)

    header = rows[0] if rows else []
    data = rows[1:] if len(rows) > 1 else []

    return JsonResponse({
        "status": "success",
        "global_index": global_index,
        "section_id": entry.get("section_id", ""),
        "section_name": entry.get("section_name", ""),
        "header": header,
        "rows": data,
    })


# Source: backend/papers/models.py — ResolvedPaper
def paper_images_view(request, pk):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    return JsonResponse({"status": "success", "images": paper.images_metadata})


# Source: backend/papers/models.py — ResolvedPaper
def paper_image_view(request, pk, idx):
    if request.method != "GET":
        return JsonResponse({"error": {"code": "METHOD_NOT_ALLOWED", "message": "Use GET."}}, status=405)

    try:
        paper = ResolvedPaper.objects.get(pk=pk)
    except ResolvedPaper.DoesNotExist:
        return JsonResponse({"status": "not_found", "message": "Paper not found."}, status=404)

    entry = next((img for img in paper.images_metadata if img.get("idx") == idx), None)
    if not entry or not entry.get("path"):
        return JsonResponse({"status": "not_found", "message": "Image not found."}, status=404)

    abs_path = os.path.join(DATA_DIR, entry["path"])
    if not os.path.exists(abs_path):
        return JsonResponse({"status": "not_found", "message": "Image file missing from disk."}, status=404)

    ext = os.path.splitext(abs_path)[1].lower()
    content_type = _IMAGE_CONTENT_TYPES.get(ext, "image/png")
    return FileResponse(open(abs_path, "rb"), content_type=content_type)

