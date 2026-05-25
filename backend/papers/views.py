from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
# Source: backend/papers/services/resolve_doi.py — resolve_doi_to_paper, fetch_sections_for_doi
from .services.resolve_doi import resolve_doi_to_paper, fetch_sections_for_doi


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

