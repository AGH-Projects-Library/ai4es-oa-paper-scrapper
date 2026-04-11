from django.shortcuts import render

# Create your views here.
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .services.resolve_doi_sections import resolve_doi_to_paper


@csrf_exempt
def resolve_doi_view(request):
    # 1. Only allow POST
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

    # 2. Parse JSON body
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

    # 3. Validate DOI
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

    # 4. Call service
    try:
        result = resolve_doi_to_paper(doi)

        # If not found, still return 200 because the request itself was valid
        if result.get("status") == "not_found":
            return JsonResponse(result, status=200)

        # On success, do NOT expose section_map in endpoint 1
        if result.get("status") == "success":
            return JsonResponse(
                {
                    "status": "success",
                    "paper": result["paper"],
                },
                status=200,
            )

        # Fallback if service returns something unexpected
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