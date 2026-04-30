# Paper Processing Pipeline

This repository contains notebooks and scripts for processing scientific papers from DOI or arXiv identifiers, converting them into Markdown, analyzing extracted sections, and exporting selected content into structured JSON format.

## Files

### `markdown_is_all_we_need.ipynb`

This notebook is used to process a large number of DOI identifiers in order to obtain Markdown versions of scientific papers.

Its main purpose is to automate the conversion of papers into `.md` files, making the content easier to inspect, analyze, and reuse in later processing steps.

---

### `histogram_section.ipynb`

This notebook is used to generate a histogram of the top 10 most frequent section names found across all Markdown files created during the processing stage.

It helps identify which article sections occur most often in the processed dataset, for example sections such as `Introduction`, `Methods`, `Results`, or `Discussion`.

---

### `to_json.ipynb`

This notebook contains the final version of the scraper and interactive exporter.

The scraper supports both **PMC articles** and **arXiv papers**. It takes DOI or arXiv identifiers as input, processes the corresponding documents, converts them into Markdown, extracts metadata, and allows selected sections to be exported into JSON format.


### `article_search.ipynb`

This notebook contains the phrase-based article search module.

It allows users to search for scientific papers using a topic phrase instead of providing exact DOI or arXiv identifiers. This is useful when the user does not know a specific paper identifier and wants to discover relevant open-access articles based on a research topic.

The notebook takes a user-provided phrase, searches for related scientific articles, collects basic metadata and available identifiers, and prepares candidate papers that can later be processed by the existing pipeline.

This module works as an additional entry point to the project. It does not replace the DOI/arXiv-based workflow, but complements it by helping users find relevant papers first.

## What `to_json.ipynb` does

The notebook performs the following tasks:

1. Creates a structured working directory called `paper_pipeline_data`, containing separate folders for:
   - Markdown files
   - downloaded PDFs
   - downloaded images
   - rendered HTML files
   - metadata files
   - final exports

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


## What `article_search.ipynb` does

The notebook performs the following tasks:

1. Accepts a topic phrase from the user.

2. Searches for scientific articles related to the provided phrase.

3. Collects basic metadata about the retrieved articles.

4. Extracts available identifiers, such as DOI or other publication-related identifiers.

5. Returns a list of candidate papers that can be reviewed by the user.

6. Allows the discovered papers to be used as input for the existing DOI/arXiv processing pipeline.

This makes the system more flexible, because users can start from a general research topic rather than a predefined list of paper identifiers.
