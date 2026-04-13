from django.urls import path
from .views import resolve_doi_view

urlpatterns = [
    path("resolve-doi/", resolve_doi_view, name="resolve-doi"),
]