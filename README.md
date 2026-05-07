# Paper Processing Pipeline

This repository contains notebooks and scripts for processing scientific papers from DOI or arXiv identifiers, converting them into Markdown, analyzing extracted sections, searching for relevant articles, and exporting selected content into structured JSON format.

The pipeline supports both interactive and batch-based workflows. Users can either manually inspect papers and select sections, or automatically extract predefined section types from a large collection of papers.

## Repository structure

```text
ai4es-oa-paper-scrapper/
├── README.md
├── notebooks/
│   ├── scraping/
│   │   ├── markdown_is_all_we_need.ipynb
│   │   └── to_json.ipynb
│   │
│   ├── export/
│   │   ├── one_zip_many_dois.ipynb
│   │   └── few_sections_many_dois.ipynb
│   │
│   ├── analysis/
│   │   └── histogram_sections.ipynb
│   │
│   └── search/
│       └── article_search.ipynb
│
├── data/
│   └── dois_test.txt
│
└── outputs/
```

## Files

### `notebooks/scraping/markdown_is_all_we_need.ipynb`

This notebook is used to process a large number of DOI identifiers in order to obtain Markdown versions of scientific papers.

Its main purpose is to automate the conversion of papers into `.md` files, making the content easier to inspect, analyze, and reuse in later processing steps.

---

### `notebooks/analysis/histogram_sections.ipynb`

This notebook is used to generate a histogram of the most frequent section names found across all Markdown files created during the processing stage.

It helps identify which article sections occur most often in the processed dataset, for example sections such as `Introduction`, `Methods`, `Results`, or `Discussion`.

The histogram is generated directly from Markdown headings. Section names are counted exactly as they appear in the Markdown files, without grouping similar section names together.

---

### `notebooks/scraping/to_json.ipynb`

This notebook contains the main interactive scraper and exporter.

The scraper supports both **PMC articles** and **arXiv papers**. It takes DOI or arXiv identifiers as input, processes the corresponding documents, converts them into Markdown, extracts metadata, and allows selected sections to be exported into JSON format.

This workflow is useful when the user wants to inspect each paper manually and decide which sections should be saved.

---

### `notebooks/export/one_zip_many_dois.ipynb`

This notebook extends the interactive export workflow for processing multiple DOI or arXiv identifiers in a single run.

The user can still interactively inspect processed documents and select specific sections, but the final export is organized as one shared batch export. Instead of creating separate ZIP archives for individual papers, the notebook creates one large ZIP file containing separate folders for each DOI or arXiv paper.

Each paper folder contains:

- a `content.json` file,
- an `images/` folder for copied figures related to the selected sections.

This notebook is useful when the user wants manual control over section selection, while still producing one clean export package for many papers.

---

### `notebooks/export/few_sections_many_dois.ipynb`

This notebook provides a batch extraction workflow for large collections of DOI or arXiv identifiers.

Instead of browsing each article manually, the user provides:

1. a list of DOI or arXiv identifiers,
2. a list of target section names, for example:
   - `methods`,
   - `introduction`,
   - `risk of bias`,
   - `conclusion`,
   - `summary`.

The notebook then automatically processes all papers and extracts sections whose headings match the requested section names.

The matching is flexible and supports similar headings. For example:

- `methods` can match `Methods` or `Materials and Methods`,
- `risk of bias` can match `Risk of Bias Assessment`,
- `conclusion` can match `Conclusions` or `Concluding Remarks`.

For each paper, the notebook creates a structured `content.json` file containing the matched sections. It also creates a batch summary file and compresses the whole result into one ZIP archive.

This workflow is useful when processing a large number of papers where the same section types need to be extracted automatically.

---

### `notebooks/search/article_search.ipynb`

This notebook contains the phrase-based article search module.

It allows users to search for scientific papers using a topic phrase instead of providing exact DOI or arXiv identifiers. This is useful when the user does not know a specific paper identifier and wants to discover relevant open-access articles based on a research topic.

The notebook takes a user-provided phrase, searches for related scientific articles, collects basic metadata and available identifiers, and prepares candidate papers that can later be processed by the existing pipeline.

This module works as an additional entry point to the project. It does not replace the DOI/arXiv-based workflow, but complements it by helping users find relevant papers first.

---

### `data/dois_test.txt`

This file contains test DOI entries that can be used as sample input for the pipeline.

It is useful for testing the scraping, conversion, and export workflows without manually entering DOI identifiers every time.

## What `notebooks/scraping/to_json.ipynb` does

The notebook performs the following tasks:

1. Creates a structured working directory called `paper_pipeline_data`, containing separate folders for:
   - Markdown files,
   - downloaded PDFs,
   - downloaded images,
   - rendered HTML files,
   - metadata files,
   - final exports.

2. Accepts one or more DOI or arXiv identifiers from the user.

3. Detects whether the input refers to:
   - an arXiv paper, or
   - a PMC article.

4. For PMC articles:
   - converts DOI to PMCID,
   - downloads PMC XML metadata,
   - extracts the article title, authors, and emails,
   - converts article sections, paragraphs, figures, and tables into Markdown,
   - downloads figure images using rendered PMC HTML through Selenium,
   - saves Markdown and metadata locally.

5. For arXiv papers:
   - extracts the arXiv ID,
   - downloads the HTML version from ar5iv,
   - converts headings, paragraphs, lists, code blocks, figures, and tables into Markdown,
   - downloads the arXiv source files,
   - extracts authors and emails from LaTeX source files,
   - saves Markdown and metadata locally.

6. Cleans the generated Markdown by removing duplicated sections.

7. Provides an interactive document viewer where the user can:
   - select a processed document,
   - browse available sections,
   - preview section text,
   - display related images,
   - print tables in a readable format,
   - choose which sections should be saved.

8. Exports selected sections into a structured `content.json` file containing:
   - article title,
   - authors,
   - emails,
   - selected sections,
   - cleaned section text,
   - extracted tables,
   - copied image paths.

9. Allows the exported content to be compressed into a `.zip` archive.

## What `notebooks/export/one_zip_many_dois.ipynb` does

The notebook performs the following tasks:

1. Accepts multiple DOI or arXiv identifiers from the user.

2. Processes each identifier using the same PMC/arXiv logic as the main scraper.

3. Creates one shared batch export directory for the entire run.

4. Creates a separate folder for each successfully processed paper.

5. Provides an interactive viewer where the user can:
   - select a document,
   - inspect available sections,
   - preview text, tables, and images,
   - manually choose sections for export.

6. Saves selected content for each paper into that paper’s own `content.json` file.

7. Copies selected section images into the corresponding paper’s `images/` folder.

8. Creates one final ZIP archive containing all exported paper folders.

The output structure is:

```text
paper_pipeline_data/
└── exports/
    └── batch_context_export_YYYYMMDD_HHMMSS/
        ├── paper_1/
        │   ├── content.json
        │   └── images/
        ├── paper_2/
        │   ├── content.json
        │   └── images/
        └── paper_3/
            ├── content.json
            └── images/
```

A ZIP archive with the same batch name is also created.

## What `notebooks/export/few_sections_many_dois.ipynb` does

The notebook performs the following tasks:

1. Accepts many DOI or arXiv identifiers from the user.

2. Allows the user to specify target section names, for example:

```text
methods, introduction, risk of bias
```

3. Processes each paper automatically.

4. Extracts available metadata such as:
   - paper identifier,
   - source type,
   - title,
   - authors,
   - emails.

5. Parses article sections from PMC XML or arXiv HTML.

6. Matches section headings against the user-provided target sections using flexible heading matching.

7. Saves matching sections into a structured `content.json` file for each paper.

8. Records unmatched requested sections, so the user can see which requested sections were not found in a given paper.

9. Creates a `batch_summary.json` file containing:
   - total number of processed documents,
   - number of successful and failed documents,
   - number of matches per requested section,
   - list of unmatched sections per paper.

10. Creates one final ZIP archive containing all extracted results.

The output structure is:

```text
paper_pipeline_data/
└── exports/
    └── batch_methods_introduction_risk_of_bias_YYYYMMDD_HHMMSS/
        ├── paper_1/
        │   └── content.json
        ├── paper_2/
        │   └── content.json
        ├── paper_3/
        │   └── content.json
        └── batch_summary.json
```

A ZIP archive with the same batch name is also created.

## What `notebooks/search/article_search.ipynb` does

The notebook performs the following tasks:

1. Accepts a topic phrase from the user.

2. Searches for scientific articles related to the provided phrase.

3. Collects basic metadata about the retrieved articles.

4. Extracts available identifiers, such as DOI or other publication-related identifiers.

5. Returns a list of candidate papers that can be reviewed by the user.

6. Allows the discovered papers to be used as input for the existing DOI/arXiv processing pipeline.

This makes the system more flexible, because users can start from a general research topic rather than a predefined list of paper identifiers.

## Output structure

After running the pipeline, the generated data is stored in:

```text
paper_pipeline_data/
├── md/
├── pdf/
├── png/
├── html/
├── meta/
└── exports/
```

Depending on the notebook used, the `exports/` directory may contain:

- individual JSON exports,
- batch export folders,
- copied images,
- batch summary files,
- ZIP archives with selected paper content.

## Typical workflows

### Workflow 1: Convert papers to Markdown

Use:

```text
notebooks/scraping/markdown_is_all_we_need.ipynb
```

This workflow is suitable when the goal is to create Markdown versions of papers for later inspection or analysis.

### Workflow 2: Analyze section frequency

Use:

```text
notebooks/analysis/histogram_sections.ipynb
```

This workflow is suitable when the goal is to understand which section headings occur most often in the processed Markdown corpus.

### Workflow 3: Manually inspect and export selected content

Use:

```text
notebooks/scraping/to_json.ipynb
```

This workflow is suitable when working with a smaller number of papers and when manual section selection is needed.

### Workflow 4: Manually inspect many papers and export one ZIP

Use:

```text
notebooks/export/one_zip_many_dois.ipynb
```

This workflow is suitable when working with multiple papers, while still manually selecting sections, and when the final result should be one combined ZIP archive.

### Workflow 5: Automatically extract selected section types from many papers

Use:

```text
notebooks/export/few_sections_many_dois.ipynb
```

This workflow is suitable when processing a large number of papers and extracting the same section types from all of them.

### Workflow 6: Search for papers by topic phrase

Use:

```text
notebooks/search/article_search.ipynb
```

This workflow is suitable when the user does not have DOI or arXiv identifiers yet and wants to find relevant papers based on a research topic.

## Path note

Because the notebooks are organized into subfolders, relative paths should be checked before running them.

If a notebook creates or reads folders such as:

```text
paper_pipeline_data/
data/
outputs/
```

it is recommended to run the notebook from the repository root or adjust path variables inside the notebook accordingly.

For example, if a notebook inside `notebooks/export/` needs to read `data/dois_test.txt`, the relative path may need to be changed to:

```text
../../data/dois_test.txt
```

depending on the current working directory used by Jupyter.
