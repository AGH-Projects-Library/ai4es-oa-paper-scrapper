from django.urls import path
from .views import resolve_doi_view, fetch_sections_view

urlpatterns = [
    path("resolve-doi/", resolve_doi_view, name="resolve-doi"),
    path("fetch-sections/", fetch_sections_view, name="fetch-sections"),
]