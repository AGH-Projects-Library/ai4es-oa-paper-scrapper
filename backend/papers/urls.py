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
    paper_export_markdown_view,
    paper_export_csv_view,
    paper_export_json_view,
    batch_export_view,
    batch_process_view,
    batch_process_upload_view,
    search_view,
    paper_rob_tables_view,
)

urlpatterns = [
    path("resolve-doi/",                               resolve_doi_view,            name="resolve-doi"),
    path("fetch-sections/",                            fetch_sections_view,         name="fetch-sections"),
    path("papers/",                                    papers_list_view,            name="papers-list"),
    path("papers/<int:pk>/",                           paper_detail_view,           name="paper-detail"),
    path("papers/<int:pk>/rob/",                       paper_rob_view,              name="paper-rob"),
    path("papers/<int:pk>/tables/",                    paper_tables_view,           name="paper-tables"),
    path("papers/<int:pk>/tables/<int:global_index>/", paper_table_detail_view,     name="paper-table-detail"),
    path("papers/<int:pk>/images/",                    paper_images_view,           name="paper-images"),
    path("papers/<int:pk>/images/<int:idx>/",          paper_image_view,            name="paper-image"),
    # Phase 2 — export endpoints
    path("papers/<int:pk>/export/markdown/",           paper_export_markdown_view,  name="paper-export-markdown"),
    path("papers/<int:pk>/export/csv/",                paper_export_csv_view,       name="paper-export-csv"),
    path("papers/<int:pk>/export/json/",               paper_export_json_view,      name="paper-export-json"),
    path("batch-export/",                              batch_export_view,           name="batch-export"),
    # Phase 3 — batch processing
    path("batch-process/",                             batch_process_view,          name="batch-process"),
    path("batch-process/upload/",                      batch_process_upload_view,   name="batch-process-upload"),
    # Phase 4 — search and ROB sub-endpoints
    path("search/",                                    search_view,                 name="search"),
    path("papers/<int:pk>/rob/tables/",                paper_rob_tables_view,       name="paper-rob-tables"),
]
