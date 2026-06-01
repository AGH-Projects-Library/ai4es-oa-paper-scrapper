# Backend State

## Active Components

| File | Purpose |
|------|---------|
| `papers/views.py` | HTTP handlers — request parsing, response formatting; no business logic |
| `papers/services/resolve_doi.py` | Orchestrates scraping + DB persistence + ROB extraction for a single DOI |
| `papers/services/rob_extraction.py` | Backend-specific ROB extraction (regex + Tesseract OCR); see note below |
| `papers/models.py` | ORM models: `ResolvedPaper`, `Section`, `Table`, `Image` |
| `backend/scraper/` | Copy of `notebooks/scraper/`; `providers.py → process_document()` is the main entry point |
| `config/settings.py` | Key setting: `SCRAPER_DATA_DIR` — base path for all file storage |

---

## API Reference

All routes are registered under `/api/` (see `config/urls.py`).

| Method | URL | Function | Source | Status |
|--------|-----|----------|--------|--------|
| POST | `/resolve-doi/` | `resolve_doi_view` | `services/resolve_doi.py — resolve_doi_to_paper()` | ✅ Active |
| POST | `/fetch-sections/` | `fetch_sections_view` | `services/resolve_doi.py — fetch_sections_for_doi()` | ✅ Active |
| GET | `/papers/` | `papers_list_view` | `models.py — ResolvedPaper` | ✅ Active |
| GET/DELETE | `/papers/<pk>/` | `paper_detail_view` | `models.py — ResolvedPaper, Section, Table, Image` | ✅ Active |
| GET | `/papers/<pk>/rob/` | `paper_rob_view` | — | ⛔ 501 Not Implemented |
| GET | `/papers/<pk>/rob/tables/` | `paper_rob_tables_view` | — | ⛔ 501 Not Implemented |
| GET | `/papers/<pk>/tables/` | `paper_tables_view` | `models.py — Table` | ✅ Active |
| GET | `/papers/<pk>/tables/<global_index>/` | `paper_table_detail_view` | `backend/scraper/parsers_md.py — parse_md_table()` (CSV variant) | ✅ Active |
| GET | `/papers/<pk>/images/` | `paper_images_view` | `models.py — Image` | ✅ Active |
| GET | `/papers/<pk>/images/<idx>/` | `paper_image_view` | `models.py — Image` | ✅ Active |
| GET | `/papers/<pk>/export/markdown/` | `paper_export_markdown_view` | `notebooks/scraper/exporters.py — compress_directory()` (in-memory variant) | ✅ Active |
| GET | `/papers/<pk>/export/csv/` | `paper_export_csv_view` | `notebooks/scraper/exporters.py — compress_directory()` (in-memory variant) | ✅ Active |
| GET | `/papers/<pk>/export/json/` | `paper_export_json_view` | `notebooks/scraper/exporters.py — export_documents()` + `models.py — DocumentInfo.to_dict()` | ✅ Active |
| POST | `/batch-export/` | `batch_export_view` | `notebooks/scraper/exporters.py — compress_directory()` (in-memory variant) | ✅ Active — supports `section_types` filter (see below) |
| POST | `/batch-process/` | `batch_process_view` | `notebooks/to_json.py — main() batch processing loop` | ✅ Active |
| POST | `/batch-process/upload/` | `batch_process_upload_view` | `notebooks/to_json.py — main() DOI file reading pattern (one DOI per line)` | ✅ Active |
| GET | `/search/` | `search_view` | Backend-specific; see note below | ✅ Active |

---

## Section Type Filtering (`POST /batch-export/`)

The client requested the ability to select a section type (introduction, methods, results, etc.)
and download those sections from every processed paper in a batch operation.

The final notebooks do not implement a formal section taxonomy. `inspect_clean_export.ipynb`
uses ad-hoc keyword filtering on section headings:

```python
df_sections[df_sections['heading'].str.contains('method', case=False, na=False)]
```

This pattern is translated to Django ORM in `batch_export_view` as:

```python
Section.objects.filter(heading__icontains=kw)
```

### API usage

```json
POST /api/batch-export/
{
  "paper_ids": [1, 2, 3],
  "section_types": ["method", "result"]
}
```

- `section_types` is optional. Omitting it exports all sections and tables (original behavior).
- Each string in `section_types` is matched as a case-insensitive substring of `Section.heading`.
- A section matches if its heading contains **any** of the supplied keywords.
- Tables from non-matching sections are also excluded.
- An empty `section_types` list returns HTTP 400.

Common keywords and what they typically match:

| Keyword | Example headings matched |
|---------|--------------------------|
| `introduction` | Introduction, Background and Introduction |
| `method` | Methods, Materials and Methods, Study Methods |
| `result` | Results, Key Results, Main Results |
| `discussion` | Discussion, General Discussion |
| `conclusion` | Conclusions, Conclusion and Future Work |
| `abstract` | Abstract |

---

## Notebook Classification

The `notebooks/` directory contains both the **current-state pipeline** and **history notebooks** kept to showcase implementation history.

### Current State (authoritative)

| File | Role |
|------|------|
| `notebooks/scraper/` (all modules) | Core scraping library — fetchers, parsers, providers, exporters, models, export_reader |
| `notebooks/to_json.py` | Batch processing entry point (`python to_json.py dois.txt`) |
| `notebooks/interactive_dois.py` | Interactive single-DOI entry point |
| `notebooks/inspect_clean_export.ipynb` | Analysis notebook using `ExportReader` |

### History Notebooks (left for reference only — not authoritative)

| File | Notes |
|------|-------|
| `notebooks/to_json.ipynb` | Pre-refactoring monolithic script (~37 k chars, single cell). Superseded by `to_json.py` + `scraper/` modules. |
| `notebooks/inspect_rob_tables_report.ipynb` | Old ROB inspection report from the `IMPLEMENTATION_GUIDE.md` era. ROB extraction removed from core pipeline per `REFACTOR_DOCUMENTATION.md`. |
| `notebooks/analyze_rob_experiments.py` | CLI-only cross-paper ROB aggregation; no backend integration. |
| `notebooks/article_search.ipynb` | Exploratory experiment. |
| `notebooks/arxiv_pubmed_all.ipynb` | Exploratory experiment. |
| `notebooks/pubmed_almost_all.ipynb` | Exploratory experiment. |
| `notebooks/display_all_tables.ipynb` | Old analysis. |
| `notebooks/from_json.ipynb` | Old analysis. |
| `notebooks/histogram_sections.ipynb` | Old analysis. |
| `notebooks/markdown_is_all_we_need.ipynb` | Old experiment. |
| `notebooks/which_sections.ipynb` | Old analysis. |
| `notebooks/BATCH_PROCESS_README.md` | Old documentation for the pre-refactor batch script. |

**Important:** `to_json.ipynb` is the pre-refactoring history file. Source comments in the backend that reference batch-processing patterns must cite `notebooks/to_json.py`, not `notebooks/to_json.ipynb`.

---

## Dead Code Removed

The following items were removed in the backend refactor. They had no active endpoint connections.

| Item | Type | Reason for removal |
|------|------|--------------------|
| `services/resolve_doi_sections.py` | Service file | Old experimental DOI resolver using bare HTTP requests. Fully superseded by `resolve_doi.py` + `scraper.providers.process_document()`. Its only unique function (`make_section_id`) already exists inline as `_make_section_id` in `resolve_doi.py`. |
| `services/rob_comparison.py` | Service file | CLI-only cross-paper ROB aggregation utility. Creates `data/` subdirectories as a side-effect of import — not safe in a Django app. Never imported by any view. |
| `services/rob_comparison_by_experiments.py` | Service file | CLI-only experiment-level ROB matrix builder. Never imported by any view. |
| `services/rob_comparison_from_export.py` | Service file | CLI-only ROB comparison from JSON export. Uses bare relative imports (`from rob_comparison import ...`) incompatible with Django packaging. |
| `services/rob_comparison_example.py` | Service file | Example driver for `rob_comparison.py`. Same bare relative import issue. |
| `services/ROB_COMPARISON_README.md` | Documentation | Documented the deleted scripts above. |
| `views.get_section_content_view` | View function | Always returned HTTP 405; had no URL route; explicitly replaced by `POST /fetch-sections/`. |
| `model.py` (backend root) | Empty file | Leftover with no content; removed. |

---

## Source Comment Policy

Source comments in this codebase track where an implementation was copied or inspired from.
They are written as:

```python
# Source: <path> — <function_name>()
```

Rules:
- A source comment linking to a notebook function does not mean the backend function is
  identical — it means that notebook function is the conceptual origin. Material differences
  should be noted in the comment.
- When no notebook analog exists (e.g. `rob_extraction.py`), no `# Source:` comment is used;
  instead a module docstring explains the origin.
- Do not add source comments for standard Django patterns (model queries, response formatting).

---

## Known Divergences from Notebook Code

| Backend item | Notebook analog | Divergence |
|---|---|---|
| `search_view` | `ExportReader.search_papers()` in `notebooks/scraper/export_reader.py` | Notebook searches by `paper_id` (configurable field) using pandas. Backend uses Django `Q` objects with `icontains` on `title` and `authors`. |
| `_make_section_id` in `resolve_doi.py` | `make_section_id()` in the now-deleted `resolve_doi_sections.py` | Inline copy; `resolve_doi_sections.py` was an intermediate backend experiment, not a notebook. |
| `rob_extraction.py` | None | Entirely backend-specific. Not called from any active code path. ROB endpoints return 501; `rob_artifacts` is always stored as `[]`. File kept for future re-implementation. |
| `batch_export_view` section filtering | `inspect_clean_export.ipynb — df['heading'].str.contains(kw, case=False)` | Same logical result; Django ORM (`heading__icontains`) instead of pandas string methods. |
| `_run_batch` / `batch_process_view` / `batch_process_upload_view` | `notebooks/to_json.py — main()` | Backend wraps `resolve_doi_to_paper()` (which calls `process_document()`) in a loop; the notebook calls `process_document()` directly and writes a timestamped JSON export. File-reading pattern (one DOI per line, skip `#` comments) is identical. |
