from django.urls import include, path

from backend.papers import admin
from .views import resolve_doi_view

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("resolve-doi/", resolve_doi_view, name="resolve-doi"),
    path("admin/", admin.site.urls),
    path("api/", include("papers.urls")),

    # OpenAPI schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]