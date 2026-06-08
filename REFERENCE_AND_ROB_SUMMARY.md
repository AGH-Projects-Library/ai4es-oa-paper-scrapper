# Reference Detection and RoB Extraction Summary

## Overview
Building upon the modular architecture established in the previous refactoring, this update introduces a comprehensive **Reference and Citation Detection Layer**. This layer enables the system to not only scrape paper content but also understand the bibliography and map specific citations to individual sections. This was primarily developed to support automated **Risk of Bias (RoB)** table identification.

### Key Finding
> **Status:** Reference detection and section-mapping work reliably across both PMC and arXiv sources. However, automated RoB table extraction based purely on these citations has proven difficult and is not performing as expected.

---

## Architectural Enhancements

### 1. Data Model Updates (`models.py`)
- **`ReferenceInfo`**: New dataclass to store bibliographic metadata (ID, text, DOI, PMID, Title, Year).
- **`SectionInfo`**: Now includes a `citations` list (strings of `ref_ids`) to track which references are mentioned in which section.
- **`DocumentInfo`**: Now stores a master list of `references`.

### 2. Source-Specific Parsing
- **PMC (`parsers_pmc.py`)**: 
    - Extracts full bibliography from XML.
    - Tracks `xref` tags within paragraphs to map citations to specific `SectionInfo` objects.
- **arXiv (`parsers_arxiv.py`)**: 
    - Parses `.tex` source files for `thebibliography` environments.
    - Implements a best-effort mapping of LaTeX `\cite{...}` commands to the sections extracted from ar5iv HTML.

### 3. Provider Integration (`providers.py`)
- The `process_document` workflow now orchestrates the extraction of references alongside the existing markdown and table extraction.
- `process_sections_and_tables` handles the injection of citation lists into the section metadata.

---

## Export Reader Enhancements (`export_reader.py`)

The `ExportReader` has been significantly upgraded to serve as an analysis tool for RoB detection:

- **`get_all_references_dataframe()`**: Flatten all bibliographies into a single searchable DataFrame.
- **`identify_rob_references()`**: Uses signature-based detection (DOIs like `10.1136/bmj.d5928` or keywords like "RoB 2") to find citations of standard bias assessment tools.
- **`get_papers_with_rob_mentions()`**: Cross-references citations and headings to find papers likely to contain RoB assessments.
- **`find_rob_tables()`**: A "smart search" function that identifies tables located in sections citing RoB tools or having RoB-related headings.
- **Updated DataFrames**: `get_all_tables_dataframe()` and `get_all_sections_dataframe()` now include citation data for context-aware filtering.

---

## Experimental Notebooks & Verification

A suite of notebooks and scripts was created to test and debug the extraction pipeline:

| File | Purpose |
|------|---------|
| `find_rob_tables.ipynb` | Core experiment for identifying RoB tables using the new citation mapping. |
| `verify_rob_references.ipynb` | Debugging tool to ensure PMC/arXiv reference IDs match the citations found in text. |
| `debug_rob_tables.ipynb` | Investigation into why table extraction fails despite successful citation detection. |

---

## Current Status & Next Steps

1.  **Reference Mapping:** ✅ **SUCCESS**  
    We can now reliably tell which paper section cites which reference.
2.  **RoB Identification:** ⚠️ **PARTIAL**  
    The system correctly identifies *where* RoB tools are mentioned, but the associated table extraction often misses the actual bias assessment data or picks up unrelated tables.
