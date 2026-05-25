from django.urls import path
from .views import (
    resolve_doi_view,
    fetch_sections_view,
    papers_list_view,
    paper_detail_view,
    paper_rob_view,
    paper_tables_view,
    paper_table_detail_view,
    paper_images_view,
    paper_image_view,
)

urlpatterns = [
    path("resolve-doi/",                               resolve_doi_view,          name="resolve-doi"),
    path("fetch-sections/",                            fetch_sections_view,       name="fetch-sections"),
    path("papers/",                                    papers_list_view,          name="papers-list"),
    path("papers/<int:pk>/",                           paper_detail_view,         name="paper-detail"),
    path("papers/<int:pk>/rob/",                       paper_rob_view,            name="paper-rob"),
    path("papers/<int:pk>/tables/",                    paper_tables_view,         name="paper-tables"),
    path("papers/<int:pk>/tables/<int:global_index>/", paper_table_detail_view,   name="paper-table-detail"),
    path("papers/<int:pk>/images/",                    paper_images_view,         name="paper-images"),
    path("papers/<int:pk>/images/<int:idx>/",          paper_image_view,          name="paper-image"),
]
