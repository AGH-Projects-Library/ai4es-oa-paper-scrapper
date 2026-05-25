# Project Overview

## What This Project Does

**ai4es-oa-paper-scrapper** is a web application that automatically retrieves, parses, and extracts structured content from open-access research papers hosted on PubMed Central (PMC) and arXiv. The primary focus is identifying **Risk of Bias (ROB)** tables and **Methods sections**, which are high-value for evidence synthesis and meta-analysis workflows.

A user provides a DOI (or arXiv identifier) through a browser UI. The system downloads the paper, converts it to structured Markdown, splits it into sections, extracts tables (saved as CSV) and images, and detects ROB-relevant content.

---

## Repository Layout

```
.
├── backend/                    # Django 5 REST API (Python 3.12)
│   ├── config/                 # Django project settings, urls, wsgi
│   ├── papers/                 # "papers" Django app
│   │   ├── models.py           # ORM models: ResolvedPaper, Section, Table, Image
│   │   ├── views.py            # All views (11 endpoints)
│   │   ├── urls.py             # URL routes
│   │   ├── migrations/         # 0001–0004 migration chain
│   │   └── services/
│   │       ├── resolve_doi.py          # Main service: DOI → scrape → DB cache → response
│   │       ├── rob_extraction.py       # ROB pattern matching & table normalization
│   │       └── rob_comparison*.py      # ROB comparison utilities (experiment-level)
│   ├── scraper/                # Copy of notebooks/scraper/ — the scraping engine
│   │   ├── models.py           # DocumentInfo, SectionInfo, TableInfo, ImageInfo dataclasses
│   │   ├── fetchers.py         # HTTP + Selenium utilities
│   │   ├── parsers_md.py       # Markdown splitting, table extraction, cleaning
│   │   ├── parsers_pmc.py      # PMC XML → Markdown
│   │   ├── parsers_arxiv.py    # arXiv HTML/TeX → Markdown + author extraction
│   │   ├── providers.py        # Orchestration: process_document()
│   │   ├── exporters.py        # JSON export (DocumentInfo list → JSON file)
│   │   └── export_reader.py    # ExportReader: load JSON → pandas DataFrames
│   ├── data/                   # Runtime output: md/, pdf/, html/, png/, tables/
│   ├── requirements.txt
│   └── Dockerfile              # python:3.12-slim + chromium + chromium-driver
├── frontend/                   # Angular 17+ SPA
│   └── src/app/
│       ├── services/doi.ts     # HTTP client: resolveDoi(), fetchSections()
│       ├── models/             # TypeScript interfaces
│       └── sections/           # UI components (stepper, hero, project description)
├── notebooks/                  # Jupyter notebooks + original scraper source
│   ├── scraper/                # Original modular scraper (keep in sync with backend/scraper/)
│   └── paper_pipeline_data/    # Notebook runtime output
├── REFACTOR_DOCUMENTATION.md   # Detailed docs for the scraper package
├── docker-compose.yml
└── TODO.txt
```

---

## The Scraper Package (`backend/scraper/`)

Copied from `notebooks/scraper/` with two backend-specific changes in `fetchers.py`:
1. Selenium imports wrapped in `try/except` so the module loads without Chrome installed
2. `get_driver()` reads `CHROMEDRIVER_PATH` env var; `Dockerfile` sets it to the apt-installed driver

### Data Models
- `DocumentInfo` — paper_id, source, authors, emails, file paths, list of sections
- `SectionInfo` — heading, `tables: List[TableInfo]`, `images: List[ImageInfo]`, `md_path`
- `TableInfo` — `csv_path`, `table_index`, `global_index`
- `ImageInfo` — `placeholder`, `caption`, `path`

### Processing Pipeline (`providers.py`)
Main entry point: `process_document(doi, base_dir)`:
1. Detects arXiv vs PMC from the DOI
2. **arXiv**: fetches rendered HTML from ar5iv.org, downloads source `.tex` for authors, downloads images
3. **PMC**: DOI → PMCID via NCBI API → OA XML → images/PDF from tar.gz (Selenium fallback for ~10 % of papers)
4. Parses Markdown into sections, saves each as its own `.md` file, tables as `.csv`
5. Returns a `DocumentInfo` with all relative paths populated

---

## Django ORM Models (`backend/papers/models.py`)

```python
class ResolvedPaper     # one row per unique DOI — the cache
class Section           # FK → ResolvedPaper; one per heading; md_path on disk
class Table             # FK → ResolvedPaper + Section; csv_path on disk
class Image             # FK → ResolvedPaper + Section; file path on disk
```

`ResolvedPaper` stores `available_sections` and `rob_artifacts` as JSONFields for fast access without joins. `Section`, `Table`, and `Image` are proper relational rows. Deleting a `ResolvedPaper` cascades through all children.

Migration chain: `0001_initial` → `0002_replace_models` → `0003_add_media_metadata` → `0004_add_table_image_models`

---

## Current API — All Implemented Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/resolve-doi/` | Scrape DOI (or return cached result), persist to DB, return paper metadata + ROB artifacts + available sections |
| POST | `/fetch-sections/` | Return markdown content for the requested section IDs; triggers scrape if DOI not yet cached |
| GET | `/papers/` | List all processed papers with counts |
| GET | `/papers/<pk>/` | Full paper detail: sections, tables, images, ROB artifacts |
| DELETE | `/papers/<pk>/` | Delete the DB record (cascades to sections, tables, images) |
| GET | `/papers/<pk>/rob/` | ROB artifacts list for this paper |
| GET | `/papers/<pk>/tables/` | Table index with section metadata |
| GET | `/papers/<pk>/tables/<global_index>/` | Parse CSV and return `{header, rows}` as JSON |
| GET | `/papers/<pk>/images/` | Image index with captions and section metadata |
| GET | `/papers/<pk>/images/<idx>/` | Serve image binary (`FileResponse`) |

### Response shapes

**`POST /resolve-doi/`** success:
```json
{
  "status": "success",
  "paper": {
    "doi": "...", "title": "...", "source": "pmc|arxiv",
    "authors": [...], "emails": [...],
    "robArtifacts": [...],
    "availableSections": [{"id": "methods", "name": "Methods"}, ...]
  }
}
```

**`POST /fetch-sections/`** success:
```json
{
  "status": "success",
  "sections": [{"id": "methods", "name": "Methods", "content": "...markdown..."}]
}
```

**`GET /papers/`** success:
```json
{
  "status": "success",
  "papers": [{"id": 1, "doi": "...", "title": "...", "source": "...", "authors": [...],
               "num_sections": 8, "num_tables": 3, "num_images": 12, "processed_at": "..."}]
}
```

### Caching logic
`resolve_doi_to_paper()` checks the DB first (fast path). If the DOI is already stored, it returns immediately without hitting any external API. `fetch_sections_for_doi()` also uses the DB fast path; it only calls `resolve_doi_to_paper()` as a fallback if the DOI is not yet cached.

### CORS
`django-cors-headers` is configured to allow `http://localhost:4200`. `CorsMiddleware` is at position 0 in the middleware stack.

---

## Implemented Features (all phases complete)

### Backend

- [x] **Export endpoints**
  - `GET /papers/<pk>/export/markdown/` → ZIP of all section `.md` files
  - `GET /papers/<pk>/export/csv/` → ZIP of all `.csv` tables
  - `GET /papers/<pk>/export/json/` → DocumentInfo-style JSON (serves snapshot from `export_json_path` or reconstructs from DB)
  - `POST /batch-export/` → `{"paper_ids": [...]}` → ZIP of all `.md` + `.csv` across multiple papers
- [x] **Batch processing**
  - `POST /batch-process/` — `{"dois": [...]}` — per-DOI results with summary counts
  - `POST /batch-process/upload/` — multipart `.txt` file (one DOI per line, `#` comments skipped)
- [x] **Search** — `GET /search/?q=...&source=pmc|arxiv`
- [x] **`DELETE /papers/<pk>/`** — removes DB rows *and* all on-disk files (md, csv, png, export JSON)
- [x] **ROB tables sub-endpoint** — `GET /papers/<pk>/rob/tables/`
- [x] **Wire `export_json_path`** — `scraper.exporters.export_documents()` called after every scrape; path stored in `ResolvedPaper.export_json_path`
- [x] **ROB image OCR** — `extract_rob_from_sections_images()` runs after markdown extraction; OCR artifacts merged before DB persist (no-op when pytesseract absent)

### Frontend

- [x] **arXiv DOI format** — validator updated to `^(\d{4}\.\d{4,5}(v\d+)?|10\.\S+\/\S+)$`
- [x] **Display ROB artifacts** — `RobArtifacts` component renders section matches and normalised table records
- [x] **Tables tab** — `TablesViewer` lazy-loads CSV data per expansion panel
- [x] **Images tab** — `ImagesViewer` renders thumbnails with captions and section badges
- [x] **Paper list view** — `PaperList` component shows all cached papers; clicking a card auto-fills DOI and triggers lookup
- [x] **Multi-DOI input** — `BatchProcessor` component with textarea + file-upload mode wired to batch-process endpoints
- [x] **Download buttons** — CSV ZIP, Markdown ZIP, JSON download buttons on step-3 results card

---

## Feature Coverage Audit: Notebooks → Backend

### Fully covered ✓

| Feature | How |
|---------|-----|
| PMC XML fetch + parse | `process_document()` called by `resolve_doi_to_paper()` |
| arXiv HTML (ar5iv) fetch + parse | Same |
| Author / email extraction | Stored in `ResolvedPaper.authors` / `.emails`, returned by `/resolve-doi/` |
| Section splitting + per-section `.md` files | `Section` rows; content served by `POST /fetch-sections/` |
| Table extraction → CSV | `Table` rows; data served by `/papers/<pk>/tables/<global_index>/` |
| Image downloading | `Image` rows; files served by `/papers/<pk>/images/<idx>/` |
| ROB detection from markdown sections + tables | `extract_rob_artifacts_from_markdown()` called on every scrape; stored in `rob_artifacts`; exposed at `/papers/<pk>/rob/` |
| ROB table normalisation (`normalize_rob_table`) | Runs inside `extract_rob_artifacts_from_markdown()`; normalised records embedded under `normalized_records` key |
| ROB extraction from images (OCR) | `extract_rob_from_sections_images()` called after markdown extraction; no-op when pytesseract absent |
| DB caching / fast-path on repeat requests | `_load_from_db()` checked before scraping |
| Paper list / detail / delete (with file cleanup) | `/papers/`, `/papers/<pk>/`, `DELETE /papers/<pk>/` |
| Batch DOI processing | `POST /batch-process/` and `POST /batch-process/upload/` |
| Export to JSON | `export_json_path` populated on every scrape; served at `/papers/<pk>/export/json/` |
| Export to ZIP | `/papers/<pk>/export/markdown/`, `/papers/<pk>/export/csv/`, `/batch-export/` |
| Cross-paper search | `GET /search/?q=...&source=pmc\|arxiv` |
| File-upload DOI list | `POST /batch-process/upload/` (multipart `.txt`) |

---

## Key Technical Notes

- All file paths in the DB are **relative to `SCRAPER_DATA_DIR`** (`backend/data/`). Views resolve them with `os.path.join(DATA_DIR, relative_path)` before opening files.
- The Selenium fallback in `fetchers.py` is only triggered when the PMC OA API does not return a tar.gz link (~10 % of papers). Chrome/chromedriver are pre-installed in the Docker image via `apt`.
- `rob_extraction.py` is production-quality. It matches 7 standard bias domains, normalises RoB 2 table structure, and optionally runs pytesseract OCR on images.
- Papers processed before migration `0004` have empty `Table` and `Image` rows. Delete and re-POST the DOI to `/resolve-doi/` to repopulate them.
- The `scraper/export_reader.py` `ExportReader` class is available for loading batch JSON exports into pandas DataFrames.
- ZIP exports are built in-memory (`io.BytesIO`) — no temporary files written to disk.
- The frontend `PaperSelectionService` signal bridges `PaperList` → `PaperSectionsStepper` without requiring a shared parent component.

---

## Future Steps

The following improvements are natural next priorities:

1. **Async batch processing** — Offload long scrapes to Celery + Redis so the HTTP response returns immediately. Add `GET /batch-jobs/<id>/` for status polling and `GET /batch-jobs/<id>/results/` for final output. The current synchronous implementation times out for batches > ~5 papers.

2. **Full-text section search** — `GET /search/` currently uses SQLite `icontains` on the title and JSON-serialised author list. Replace with SQLite FTS5 (via `django-fts`) or an Elasticsearch index to support searching *inside* section markdown content.

3. **Authentication & multi-tenancy** — Add user accounts (Django Allauth or JWT) so different researchers have isolated paper collections. The `ResolvedPaper` model needs a `user` FK; the paper list and delete endpoints should enforce ownership.

4. **Citation graph** — Extract `<ref>` elements from PMC XML and DOI links from arXiv HTML. Store references as a `Reference` model (FK paper → FK cited paper or raw DOI string) and expose `GET /papers/<pk>/references/` to power a citation-network visualisation.

5. **Systematic-review export formats** — Add PRISMA-compatible CSV, RIS, and BibTeX export so results can be imported directly into Covidence, Rayyan, or Zotero. `GET /papers/<pk>/export/ris/` is the minimal addition needed.

6. **Paper versioning** — Track arXiv paper versions (v1 → v2 → v3). Store `arxiv_version` on `ResolvedPaper`; add a `POST /papers/<pk>/refresh/` endpoint that re-scrapes and diffs sections between versions.

7. **Test coverage** — Unit tests for `scraper/parsers_pmc.py`, `scraper/parsers_arxiv.py`, and `rob_extraction.py` using `pytest`. Integration tests for the Django API using `django.test.TestClient` with fixture-based DOI mocking so tests run without network access.

8. **Docker production hardening** — Replace the development server with gunicorn behind nginx. Switch SQLite to PostgreSQL (needed for concurrent writes during batch processing). Manage secrets via environment variables injected at runtime, not baked into the image.
