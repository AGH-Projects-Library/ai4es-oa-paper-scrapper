# OA Paper Scraper

A full-stack pipeline for retrieving and extracting structured content from open-access research papers. Given one or more DOIs, the system downloads papers from PubMed Central (PMC) or arXiv, parses them into structured Markdown, splits them into sections, extracts tables and images, and identifies **Risk of Bias (ROB)** content — producing outputs ready for evidence synthesis and meta-analysis.

<!-- screenshot: web UI hero section with DOI input -->

---

## Features

- **Multi-source fetching** — PMC via OA API + XML, arXiv via ar5iv HTML + TeX source; Selenium fallback for PMC papers without a tar.gz link (~10%)
- **Structured extraction** — sections, tables (CSV), images, author names and email addresses
- **Risk of Bias detection** — regex + OCR (pytesseract) matching across 7 standard bias domains; normalized RoB 2 table records
- **DB caching** — repeat lookups for the same DOI return immediately without hitting external APIs
- **Batch processing** — submit a list of DOIs via JSON body or upload a `.txt` file; section-type filtering on exports
- **Export formats** — per-paper or batch ZIP (Markdown, CSV), JSON snapshot
- **Angular SPA** — stepper UI, paper list, tables/images viewer, ROB display, download buttons, batch processor with file upload

<!-- screenshot: stepper result card showing sections, tables, and ROB artifacts -->

---

## Quick Start (Docker)

```bash
git clone <repo-url>
cd ai4es-oa-paper-scrapper
docker compose up --build
```

| Service  | URL                    |
|----------|------------------------|
| Frontend | http://localhost:4200  |
| Backend  | http://localhost:8000  |

---

## Repository Layout

```
.
├── backend/                        # Django 5 REST API (Python 3.12)
│   ├── config/                     # settings, urls, wsgi/asgi
│   ├── papers/                     # "papers" Django app
│   │   ├── models.py               # ResolvedPaper, Section, Table, Image
│   │   ├── views.py                # All API views
│   │   ├── urls.py
│   │   ├── migrations/             # 0001–0004
│   │   └── services/
│   │       ├── resolve_doi.py      # DOI → scrape → DB persist → response
│   │       └── rob_extraction.py   # ROB pattern matching & OCR
│   ├── scraper/                    # Scraping engine (mirrors notebooks/scraper/)
│   │   ├── models.py               # DocumentInfo, SectionInfo, TableInfo, ImageInfo
│   │   ├── fetchers.py             # HTTP, Selenium, NCBI API utilities
│   │   ├── parsers_md.py           # Markdown splitting and table extraction
│   │   ├── parsers_pmc.py          # PMC XML → Markdown
│   │   ├── parsers_arxiv.py        # arXiv HTML/TeX → Markdown + author extraction
│   │   ├── providers.py            # process_document() — main entry point
│   │   ├── exporters.py            # JSON export
│   │   └── export_reader.py        # ExportReader: JSON → pandas DataFrames
│   ├── data/                       # Runtime output: md/, pdf/, html/, png/, tables/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                       # Angular 19 SPA
│   └── src/app/
│       ├── services/               # HTTP client (doi.ts, paper-selection.service.ts)
│       ├── models/                 # TypeScript interfaces
│       └── sections/               # UI components
│           ├── hero-section/
│           ├── paper-list/
│           ├── paper-sections-stepper/
│           │   ├── rob-artifacts/
│           │   ├── tables-viewer/
│           │   └── images-viewer/
│           ├── batch-processor/
│           └── project-description/
├── notebooks/                      # Original scraper source + Jupyter notebooks
│   ├── scraper/                    # Canonical scraper library (keep in sync with backend/scraper/)
│   ├── to_json.py                  # Batch entry point: python to_json.py dois.txt
│   ├── interactive_dois.py         # Interactive single-DOI entry point
│   └── inspect_clean_export.ipynb  # Analysis notebook using ExportReader
├── data/                           # Sample DOI lists
└── docker-compose.yml
```

---

## Processing Pipeline

```
DOI input
   │
   ▼
providers.process_document(doi, base_dir)
   ├── arXiv?  → fetch ar5iv HTML + TeX source → parse → save md/html/png
   └── PMC?    → DOI → PMCID (NCBI API) → OA XML + tar.gz → [Selenium fallback] → save md/html/pdf/png
   │
   ▼
parse_markdown() — split into sections, extract tables (CSV), map image refs
   │
   ▼
extract_rob_artifacts_from_markdown() — ROB pattern matching + normalize_rob_table()
extract_rob_from_sections_images()    — optional pytesseract OCR on figures
   │
   ▼
DB persist: ResolvedPaper → Section → Table / Image rows
   │
   ▼
JSON response → Angular SPA
```

---

## API Reference

All routes are prefixed with `/api/`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/resolve-doi/` | Scrape DOI (or return DB cache); returns paper metadata + ROB + available sections |
| POST | `/fetch-sections/` | Return Markdown content for requested section IDs |
| GET | `/papers/` | List all processed papers with counts |
| GET | `/papers/<pk>/` | Full paper detail: sections, tables, images, ROB |
| DELETE | `/papers/<pk>/` | Delete DB record and all on-disk files |
| GET | `/papers/<pk>/rob/` | ROB artifacts list |
| GET | `/papers/<pk>/tables/` | Table index with section metadata |
| GET | `/papers/<pk>/tables/<global_index>/` | Table data as `{header, rows}` JSON |
| GET | `/papers/<pk>/images/` | Image index with captions |
| GET | `/papers/<pk>/images/<idx>/` | Serve image binary |
| GET | `/papers/<pk>/export/markdown/` | ZIP of all section `.md` files |
| GET | `/papers/<pk>/export/csv/` | ZIP of all `.csv` tables |
| GET | `/papers/<pk>/export/json/` | DocumentInfo-style JSON snapshot |
| POST | `/batch-export/` | ZIP of md + csv across multiple papers; supports `section_types` filter |
| POST | `/batch-process/` | Process a list of DOIs; returns per-DOI results |
| POST | `/batch-process/upload/` | Upload `.txt` file (one DOI per line, `#` comments skipped) |
| GET | `/search/?q=&source=` | Full-text search across title and authors |

### Key request/response shapes

**`POST /resolve-doi/`**
```json
{ "doi": "10.1186/s13601-019-0278-3" }
```
```json
{
  "status": "success",
  "paper": {
    "doi": "...", "title": "...", "source": "pmc",
    "authors": ["..."], "emails": ["..."],
    "robArtifacts": [...],
    "availableSections": [{"id": "methods", "name": "Methods"}, ...]
  }
}
```

**`POST /batch-export/`** with section filtering
```json
{
  "paper_ids": [1, 2, 3],
  "section_types": ["method", "result"]
}
```
Section keywords are matched case-insensitively against `Section.heading`. Omitting `section_types` exports everything.

---

## Notebook Usage

### Batch processing (CLI)

```bash
cd notebooks
python to_json.py ../data/dois_test.txt
```

**DOI file format:**
```
# Comments are ignored
10.1186/s13601-019-0278-3
2401.00456
10.1101/2023.01.01.100001
```

Output is written to `notebooks/paper_pipeline_data/exports/processed_export_<timestamp>.json`.

### Interactive (single DOI)

```bash
python notebooks/interactive_dois.py
```

### Analysis notebook

```bash
jupyter notebook notebooks/inspect_clean_export.ipynb
```

Uses `ExportReader` to load the latest JSON export into pandas DataFrames:

```python
from scraper.export_reader import load_latest_export

reader = load_latest_export()
reader.print_summary()

df_docs    = reader.get_documents_dataframe()
df_tables  = reader.get_all_tables_dataframe()
df_images  = reader.get_all_images_dataframe()

# Load a specific table
df = reader.load_table_csv('tables/PMC6706894/table_0.csv')

# Filter by section keyword
methods = reader.get_all_sections_dataframe()
methods = methods[methods['heading'].str.contains('method', case=False)]
```

---

## Output File Structure

```
paper_pipeline_data/               (or backend/data/ when served via the API)
├── exports/
│   └── processed_export_<timestamp>.json
├── md/
│   └── PMC6706894/
│       ├── full_document.md
│       └── sections/
│           ├── section_000_abstract.md
│           ├── section_001_introduction.md
│           ├── section_002_methods.md
│           └── ...
├── html/
├── pdf/
├── png/
│   └── PMC6706894/
│       └── figure_001.jpg
└── tables/
    └── PMC6706894/
        ├── table_0.csv
        └── table_1.csv
```

All paths in the JSON export are **relative** to the base directory. `ExportReader` resolves them automatically.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Django 5, Django REST Framework |
| Frontend | Angular 19, Angular Material |
| Scraping | requests, BeautifulSoup4, lxml, Selenium, webdriver-manager |
| Data | pandas, pytesseract (optional OCR) |
| Infrastructure | Docker, docker-compose |
| Storage | SQLite (dev), on-disk files for md/csv/png/pdf |

---

## Development (without Docker)

**Backend**
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npx ng serve
```

**CORS** is pre-configured for `http://localhost:4200`.

---

## Extending to a New Source

1. Add fetch functions to `scraper/fetchers.py`
2. Add a `parsers_<source>.py` module
3. Add a `process_<source>()` function in `scraper/providers.py`
4. Register it in the `process_document()` router

---

## Data Sources

Papers are fetched from:

- **PubMed Central** — via NCBI OAI-PMH XML + Open Access tar.gz
- **arXiv** — via ar5iv.org rendered HTML + TeX source

<!-- screenshot: batch processor component -->
