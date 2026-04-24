from django.urls import path
from .views import resolve_doi_view
from .views import get_section_content_view

urlpatterns = [
    path("resolve-doi/", resolve_doi_view, name="resolve-doi"),
    path('section/<str:section_id>/', get_section_content_view, name="get-section"),
]