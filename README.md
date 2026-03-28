# Scrapping information from Open-Access Research Papers

This is not a final readme but a reminder what this project is all about.

## Running the project

To run this project you need to have docker installed and run:

```Bash
docker compose up --build
```

in the repository.

## Short description

This project aims to build a pipeline for retrieving and extracting selected information from open-access research papers available online. The main focus is on identifying and extracting Risk of bias information and the Methods section from full-text articles hosted in repositories such as PubMed Central, arXiv, and medRxiv. The system should download articles from identifiers such as DOI or repository IDs, parse them into a structured machine-readable form, and detect the relevant content using document structure, pattern matching, and, where useful, NLP methods.

The extracted results should be suitable for comparison across multiple papers and exportable in a structured format such as CSV. The project may reuse and extend the previous year’s repository. A practical end result could be a browser-based web application that accepts one DOI or a collection of DOIs and returns extracted information for downstream evidence synthesis and literature review workflows.
## General idea of the project

As part of ongoing work on using AI for evidence synthesis and knowledge retrieval, this project focuses on the **automated extraction of selected information from open-access research papers** available online, especially from repositories such as PubMed Central, arXiv, and medRxiv.

The project is focused primarily on retrieving the following section:

- Risk of bias information, especially risk-of-bias tables and related content,
- Methods / methodology sections,
- and, secondarily, standard paper sections such as Introduction or Results.

Another tiny task is to retrieve the email addresses of first, last, and corresponded author. 

The ultimate goal is to create a reliable pipeline and practical tool that can download papers, identify the relevant fragments, and export structured results for downstream tasks such as evidence synthesis, meta-analysis support, and AI-assisted literature review.

There is also interest in making the result practical from a user perspective, ideally as a web application working in the browser, where the user can provide a single DOI or a collection of DOIs and export the extracted data, for example to CSV.

The project is best described as a system for:

1. Fetching open-access papers from online sources,
2. Parsing them into a structured form,
3. Locating specific content of interest, with the strongest emphasis on risk of bias and methods,
4. Extracting structured outputs that can later be compared across many papers.

So the project is less about generic NLP over all paper content, and more about reliably retrieving a small number of high-value elements from full-text research articles.

---

## Stage 1: Collecting and parsing papers from open repositories

The first stage is to obtain a paper and transform it into a machine-readable representation.

Possible inputs may include:

- DOI,
- URL,
- PubMed Central identifier,
- arXiv identifier,
- possibly a list of such identifiers.

However at first a single DOI or a list of DOIs will be sufficient.

The pipeline should then:

1. Download or retrieve the paper from an open-access source,
2. Parse the document into a structured representation,
3. Separate headings, paragraphs, tables, and possibly figures,
4. Preserve metadata such as title, authors, abstract, DOI, and source,
5. Keep enough structure to support later detection of Methods and Risk of bias content.

A key clarification from the discussion is that **arXiv provides an HTML version of papers**, so the system does not need to rely only on PDFs there. In general, formats such as HTML or XML will likely be easier to process than PDF whenever available.

### Example structured output

```json
{
  "paper_id": "...",
  "title": "...",
  "source": "...",
  "doi": "...",
  "authors": ["..."],
  "sections": [
    {"heading": "Introduction", "text": "..."},
    {"heading": "Methods", "text": "..."}
  ],
  "tables": [
    {"caption": "Risk of bias assessment", "content": "..."}
  ]
}
```

---

## Stage 2: Detecting and extracting the target content

This stage should focus mainly on the extraction of:

- Risk of bias content, especially tables,
- Methods / methodology,
- and possibly selected standard sections.

However the **Risk of bias** is the central focus.

This includes content such as:

- evaluations of potential bias at different stages of the study,
- systematic sources of error,
- items such as whether blinding was used,
- tables checking multiple types of bias for a given study design,
- material that supports later comparison across articles.

Because of that, the extraction should not be limited to plain section headers. In many cases, the relevant information may appear in:

- section text,
- tables,
- figure-like structured elements,
- or patterns in the document layout.

The first versions of the system can rely on relatively simple approaches such as:

- string matching,
- pattern matching,
- rule-based detection,
- structural heuristics for tables and graphs,

rather than immediately requiring a heavy ML or LLM-based solution.

---

## Stage 3: Evaluation

The practical evaluation questions could be:

- Did the system locate the correct Risk of bias content?
- Did it correctly capture the table or structured element?
- Did it miss relevant parts of the Methods section?
- Is the exported result complete enough for later comparison across papers?

---

## Use of previous work

The project may be based fully on the [previous repository](https://github.com/AGH-Projects-Library/ai4es-eligibility-criteria-generation)

---

## Sources and repositories

The project focuses on papers from :

- arXiv,
- medRxiv,
- and possibly other open-access article sources.

This means the system should be designed with multiple sources in mind, not just one repository.