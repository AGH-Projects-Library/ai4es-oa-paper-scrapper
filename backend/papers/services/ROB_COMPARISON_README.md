# Complete ROB Analysis Workflow Guide

## Overview

Complete end-to-end workflow for processing academic papers, extracting Risk of Bias (ROB) data, and analyzing ROB assessments across multiple papers.

### Three Main Tools

1. **`batch_process_dois.py`** (notebooks/) - Non-interactive batch processor for scraping papers from DOI list
2. **`rob_comparison_from_export.py`** (backend/papers/services/) - Cross-paper ROB comparison and conflict detection
3. **`analyze_rob_experiments.py`** (notebooks/) - Experiment-focused ROB analysis (study-level assessments)

### Supporting Modules

- **`rob_comparison.py`** - Core comparison algorithms (imported by analysis scripts)
- **`rob_comparison_example.py`** - Example with sample data (for testing)
- **`rob_extraction.py`** - ROB text/table/image extraction engine

## Quick Start (5 Steps)

```bash
# 1. Create DOI list
cat > my_dois.txt << EOF
10.3389/falgy.2023.1211949
10.1038/s41591-023-02123-6
10.1145/3452383
EOF

# 2. Process papers
cd notebooks
python batch_process_dois.py my_dois.txt

# 3. Cross-paper comparison
cd ../backend/papers/services
python rob_comparison_from_export.py ../../../notebooks/exports/processed_export_*.json

# 4. Experiment-focused analysis
cd ../../notebooks
python analyze_rob_experiments.py ../paper_pipeline_data/exports/processed_export_*.json

# 5. Explore results
cat ../paper_pipeline_data/exports/processed_export_*_experiment_report.json | jq '.conflicting_experiments'
```

---

## Part 1: Batch Processing with `batch_process_dois.py`

### Purpose

Automates scraping of academic papers from DOI identifiers, extracting content, and generating structured JSON export with ROB artifacts. Replaces interactive `to_json.py` with non-interactive batch processing.

### Location
`notebooks/batch_process_dois.py`

### Usage

```bash
cd notebooks
python batch_process_dois.py <path_to_dois_file>
```

### Input File Format

Text file with one DOI per line. Comments and empty lines are ignored:

```
10.3389/falgy.2023.1211949
10.48550/arXiv.2603.24132
# Comments starting with # are ignored

# Empty lines above are ignored
10.1145/3452383
```

**Features:**
- ✅ One DOI per line
- ✅ Comments starting with `#` are ignored
- ✅ Empty lines are ignored
- ✅ Works with relative or absolute paths

### Processing Flow

```
Input: my_dois.txt (5 DOIs)
  ↓
[1/5] Processing: 10.3389/falgy.2023.1211949
  → Auto-detect: arXiv or PMC?
  → If arXiv: Download from arXiv
  → If PMC/PubMed:
      → Try fast OA API extraction (80% success, ~10 sec)
      → If fails: Fall back to Selenium browser (~30 sec)
  → Extract markdown, images, metadata
  → Extract ROB artifacts from content
  ✅ Success
  ↓
[2/5] Processing: 10.1038/s41591-023-02123-6
  → [Similar process]
  ✅ Success
  ↓
... continue for remaining papers ...
  ↓
✅ 5/5 papers processed successfully
  ↓
Export complete: paper_pipeline_data/exports/processed_export_1234567890.json
```

### Output Files (3 Files Generated)

#### 1. Main Export: `processed_export_<timestamp>.json`

**Location:** `paper_pipeline_data/exports/`

**Format:** JSON array of paper objects

**Structure example:**
```json
[
  {
    "paper_id": "10.3389/falgy.2023.1211949",
    "source": "pubmed",
    "pmcid": "PMC10054609",
    "extraction_method": "oa_api",
    "md_path": "backend/data/md/PMC10054609.md",
    "html_path": "backend/data/html/PMC10054609.html",
    "authors": ["Green, M.", "Smith, J."],
    "emails": ["m.green@example.com"],
    "local_images": ["backend/data/png/PMC10054609/figure1.png"],
    "sections": [
      {
        "heading": "Methods",
        "tables": [
          {
            "header": ["Column 1", "Column 2"],
            "rows": [["Value 1", "Value 2"]],
            "markdown": "| Column 1 | Column 2 |..."
          }
        ],
        "images": [
          {
            "placeholder": "PMC_FIG_1",
            "caption": "Study design figure",
            "path": "backend/data/png/PMC10054609/figure1.png"
          }
        ]
      }
    ],
    "rob_artifacts": [
      {
        "artifact_type": "table",
        "section": "Risk of Bias Assessment",
        "match": "RoB 2: ...",
        "normalized_records": [
          {
            "bias_domain": "selection",
            "bias_value": "high",
            "study_name": "Green",
            "column_header": "Randomization Process",
            "row_index": 0,
            "confidence": 0.95
          }
        ],
        "confidence": 0.95
      }
    ]
  }
]
```

**Key fields:**
- `extraction_method`: `"oa_api"` (fast, no browser) or `"selenium"` (slower, requires rendering)
- `source`: Always `"pubmed"` for PMC papers, `"arxiv"` for arXiv
- `rob_artifacts`: ROB data extracted from paper (may be empty if no ROB found)
- `sections`: Structured paper content with tables and images
- `local_images`: Paths to downloaded figure files

#### 2. ROB Papers List: `processed_export_<timestamp>_rob_dois.txt`

**Format:** One DOI per line (DOIs only, no additional metadata)

**Example:**
```
10.3389/falgy.2023.1211949
10.1038/s41591-023-02123-6
10.1145/3452383
10.48550/arXiv.2401.12345
```

**Use case:** 
- Track which papers contain ROB data
- Filter for downstream analysis
- Create subset for specialized processing

#### 3. OA-Only ROB Papers: `processed_export_<timestamp>_rob_oa_only_dois.txt`

**Format:** One DOI per line (DOIs only, papers extracted via OA API)

**Example:**
```
10.3389/falgy.2023.1211949
10.1038/s41591-023-02123-6
10.48550/arXiv.2401.12345
```

**Use case:** 
- Identify papers that don't need Selenium (faster extraction method)
- Re-process papers without browser overhead
- Suitable for high-throughput workflows

### What Gets Extracted

#### From PMC Papers

1. **Metadata:** Authors, affiliations, emails
2. **Content:** Full markdown of article with structure preserved
3. **Images:** All figures extracted and saved locally
4. **HTML:** Rendered or cached HTML (for reference)
5. **ROB artifacts:** Risk of bias tables, sections, and image-based data

#### From arXiv Papers

1. **Metadata:** Authors, title, abstract
2. **PDF:** Downloaded and stored
3. **Content:** Extracted from PDF as markdown
4. **Limited images:** arXiv data is less rich than PMC

### Extraction Methods: OA API vs Selenium

**OA API (Preferred):**
- Speed: ~5-15 seconds per paper
- Success rate: ~80%
- Requirements: Network access only
- Data: Images, HTML, metadata from tar.gz archives
- Returns: `extraction_method = "oa_api"`

**Selenium (Fallback):**
- Speed: ~20-40 seconds per paper
- Success rate: ~95%
- Requirements: Headless Chrome browser
- Data: Full rendered HTML with JavaScript execution
- Returns: `extraction_method = "selenium"`

### Changes to `to_json.py`

**Modified `download_pmc_images()`:**
```python
def download_pmc_images(pmcid):
    """Returns: (local_paths, html_path, extraction_method)"""
    
    # Try OA API first
    oa_paths = extract_images_from_oa(pmcid)
    if oa_paths is not None:
        return oa_paths, html_path, "oa_api"  # ← Fast extraction
    
    # Fall back to Selenium
    html = fetch_real_html_pmc(pmcid)
    # ... download images ...
    return local_paths, html_path, "selenium"  # ← Slower extraction
```

**Updated `process_pmc()`:**
```python
def process_pmc(doi):
    # ...
    local_images, html_path, extraction_method = download_pmc_images(pmcid)
    
    meta = {
        "paper_id": doi,
        "source": "pubmed",  # Changed from "pmc"
        "extraction_method": extraction_method,  # ← NOW TRACKED
        # ... other fields ...
    }
    save_json(meta, meta_path)
    return meta
```

**Updated `export_all_processed_json()`:**
```python
for doc in out:
    if doc.get("rob_artifacts"):
        paper_id = doc.get("paper_id")
        rob_papers.append(paper_id)
        
        # Separate OA-only papers (no Selenium)
        if doc.get("extraction_method") == "oa_api":
            oa_only_rob_papers.append(paper_id)

# Write simple DOI-only lists
with open(rob_list_path, "w") as f:
    for paper_id in rob_papers:
        f.write(f"{paper_id}\n")

with open(oa_rob_list_path, "w") as f:
    for paper_id in oa_only_rob_papers:
        f.write(f"{paper_id}\n")
```

---

## Part 2: Cross-Paper ROB Comparison with `rob_comparison_from_export.py`

### Purpose

Compares ROB assessments across multiple papers to identify:
- **Consensus**: Which bias domains papers agree on
- **Conflicts**: Where papers disagree
- **Coverage**: Which domains appear in which papers
- **Patterns**: Common assessment methodologies

### Location
`backend/papers/services/rob_comparison_from_export.py`

### Usage

```bash
cd backend/papers/services
python rob_comparison_from_export.py ../../../notebooks/exports/processed_export_<timestamp>.json
```

### Input

**File:** JSON export from `batch_process_dois.py`

**Expected structure:** Array of paper objects with `rob_artifacts` field

### Processing Flow

```
Input JSON: 146 papers
  ↓
For each paper:
  For each ROB artifact:
    For each normalized_record:
      Extract: (bias_domain, paper_id, bias_value)
  ↓
Build alignment matrix:
  bias_domain × papers → {domain: {paper1: value1, paper2: value2, ...}}
  ↓
For each bias domain:
  Calculate: consensus_value (majority vote)
  Calculate: agreement_rate (% papers agreeing)
  Detect: conflicts (unique_values > 1)
  ↓
Generate report:
  - Summary statistics
  - Domain alignment matrix
  - Detected conflicts
  - Coverage analysis
  - Recommendations
```

### Output: Console Report

Example output:

```
================================================================================
ROB ASSESSMENT COMPARISON REPORT
================================================================================

SUMMARY:
  Papers analyzed: 146
  Total ROB artifacts: 312
  - Table artifacts: 289
  - Text section artifacts: 18
  - OCR image artifacts: 5

BIAS DOMAIN ALIGNMENT:
  ✓ selection:        89 papers → low (95% agree)
  ✓ performance:      87 papers → high (78% agree)
  ⚠ detection:        82 papers → unclear (56% agree) [CONFLICT]
  ✗ attrition:        45 papers → low (65% agree) [CONFLICT]
  ✓ reporting:       103 papers → high (88% agree)
  ✓ bias_in_conduct:  95 papers → high (82% agree)

DETECTED CONFLICTS (papers disagree on bias score):
  1. detection: 82 papers assessed
     - "high" (24 papers)
     - "unclear" (46 papers) ← MAJORITY
     - "low" (12 papers)

  2. attrition: 45 papers assessed
     - "low" (29 papers) ← MAJORITY
     - "unclear" (16 papers)

POPULAR ASSESSMENT SECTIONS:
  1. "Risk of Bias Assessment" (92 papers)
  2. "Assessment of Risk of Bias" (68 papers)
  3. "Study Quality" (24 papers)

RECOMMENDATIONS:
  ✓ High consensus detected on selection bias (95% agreement)
  ⚠ Review methodology differences in detection bias assessment
  ⚠ Low coverage on attrition bias (only 45 papers)
  ⚠ Consider OCR fallback for papers lacking explicit attrition assessment
```

### Output: JSON Report - `rob_comparison_real_data_report.json`

**Location:** `backend/papers/services/`

**Structure:**
```json
{
  "summary": {
    "num_papers": 146,
    "total_artifacts": 312,
    "total_text_artifacts": 18,
    "total_table_artifacts": 289,
    "total_ocr_artifacts": 5
  },
  "table_alignment": {
    "domain_matrix": {
      "selection": {
        "10.3389/falgy.2023.1211949": "high",
        "10.1038/s41591-023-02123-6": "low",
        "10.1145/3452383": "high"
      },
      "performance": {
        "10.3389/falgy.2023.1211949": "high",
        "10.1038/s41591-023-02123-6": "high"
      },
      "detection": {
        "10.3389/falgy.2023.1211949": "high",
        "10.1038/s41591-023-02123-6": "unclear"
      }
    },
    "conflicts": [
      {
        "bias_domain": "detection",
        "unique_values": ["high", "unclear", "low"],
        "paper_count": 82,
        "conflict_papers": [
          {
            "paper_id": "10.1234/example.1",
            "value": "high"
          },
          {
            "paper_id": "10.5678/example.2",
            "value": "unclear"
          }
        ]
      }
    ],
    "coverage": {
      "selection": 89,
      "performance": 87,
      "detection": 82,
      "attrition": 45
    },
    "summary": {
      "selection": {
        "consensus_value": "low",
        "agreement_rate": 0.95,
        "coverage": 89,
        "unique_values": ["low"]
      },
      "detection": {
        "consensus_value": "unclear",
        "agreement_rate": 0.56,
        "coverage": 82,
        "unique_values": ["high", "unclear", "low"]
      }
    }
  },
  "section_artifacts": {
    "by_section": {
      "Risk of Bias Assessment": [
        {
          "paper_id": "10.3389/falgy.2023.1211949",
          "artifact_id": "section_1",
          "confidence": 0.92
        }
      ]
    },
    "popular_sections": [
      ["Risk of Bias Assessment", 92],
      ["Assessment of Risk of Bias", 68],
      ["Study Quality", 24]
    ]
  },
  "ocr_artifacts": {
    "total_ocr_artifacts": 5,
    "average_confidence": 0.78,
    "methods_used": {"ocr_table": 3, "ocr_text": 2}
  },
  "recommendations": [
    {
      "type": "high_consensus",
      "message": "selection bias shows 95% agreement across papers - reliable consensus",
      "domain": "selection"
    },
    {
      "type": "investigate_conflicts",
      "message": "detection bias shows conflicting assessments",
      "conflicts": 1,
      "domain": "detection"
    }
  ]
}
```

### Interpreting Results

**Agreement Rate:**
- `1.0` (100%) = All papers assess this domain identically
- `0.75-0.99` (75-99%) = Strong consensus (reliable)
- `0.50-0.74` (50-74%) = Mixed opinion (investigate differences)
- `<0.50` (<50%) = No clear consensus (check methodologies)

**Coverage:**
- High (>80% of papers) = Common assessment criterion
- Medium (50-80%) = Standard but not universal
- Low (<50%) = Some papers use different assessment tools

**Conflicts:**
Detected when papers assess the same bias domain with different values. Usually indicates:
- Different RoB assessment tools used (RoB2 vs ROBINS-I, etc.)
- Different assessment methodologies or criteria
- Different inclusion/exclusion criteria for papers
- Legitimate disagreement in bias assessment

**Recommendations:**
- **high_consensus**: Majority voting shows strong agreement
- **investigate_conflicts**: Review methodological differences
- **high_confidence_ocr**: OCR results are reliable (>0.7 confidence)
- **review_low_confidence**: Manual review needed for OCR (<0.7)
- **improve_coverage**: Some domains appear in few papers

---

## Part 3: Experiment-Focused Analysis with `analyze_rob_experiments.py`

### Purpose

Analyzes ROB data organized by **experiments** (study names from RoB2 tables). Answers:
- Which studies appear in multiple papers?
- Do papers agree on ROB assessment for the same study?
- Which studies have consensus vs. conflicts?

### Location
`notebooks/analyze_rob_experiments.py`

### What Are "Experiments"?

In systematic reviews, RoB2 tables typically have row labels representing studies:

**Example RoB2 table structure:**
```
┌──────────────────────────────────────────────────────────┐
│ Risk of Bias Assessment Table                            │
├──────────┬──────────┬────────┬──────────┬──────────┐
│ Study    │ Random.  │ Deviat │ Missing  │ Select   │
│ Name     │ Process  │ ions   │ Outcome  │ Reported │
├──────────┼──────────┼────────┼──────────┼──────────┤
│ Green    │ High     │ High   │ Low      │ High     │
│ Tiffany  │ Low      │ Low    │ Low      │ High     │
│ Bloch    │ Low      │ Low    │ Low      │ Low      │
│ Davis    │ High     │ High   │ High     │ Unclear  │
└──────────┴──────────┴────────┴──────────┴──────────┘

Column 0 = Study Name ("Green", "Tiffany", "Bloch", "Davis")
Columns 1+ = Bias domains for each study
```

**"Green", "Tiffany", "Bloch", "Davis" are experiments** - they're the study/trial identifiers being assessed for bias.

### Usage

```bash
cd notebooks
python analyze_rob_experiments.py ../paper_pipeline_data/exports/processed_export_<timestamp>.json
```

### Input

**File:** JSON export from `batch_process_dois.py` (same as rob_comparison_from_export.py)

**Expected structure:** Array of paper objects with `rob_artifacts` containing normalized_records

### Processing Flow

```
Input JSON: 146 papers with ROB artifacts
  ↓
For each paper:
  For each ROB artifact:
    For each normalized_record:
      Extract: study_name (e.g., "Green", "Smith", "Bloch")
      Extract: bias_domain, bias_value
      Store: experiments[study_name][domain] = value
  ↓
Build experiment matrix:
  For each unique study_name:
    For each bias domain:
      Collect all papers assessing (study, domain)
      Calculate: consensus_value (majority vote)
      Calculate: agreement_rate (% consensus)
      Detect: conflicts (unique_values > 1)
  ↓
Categorize:
  - High agreement experiments (>75% consensus)
  - Conflicting experiments (disagreements detected)
  ↓
Generate report
```

### Output: Console Report

**Example output:**

```
================================================================================
ROB ASSESSMENT REPORT BY EXPERIMENTS
================================================================================

Overall Statistics:
  Papers analyzed: 146/146
  Unique experiments: 78
  Experiments with conflicts: 5
  Experiments with high agreement: 68

HIGH AGREEMENT EXPERIMENTS (>75% consensus):
  ✓ Green (100% agreement)
  ✓ Smith (92% agreement)
  ✓ Johnson (88% agreement)
  ✓ Williams (91% agreement)
  ... (64 more experiments with >75% agreement)

CONFLICTING EXPERIMENTS (varying ROB assessments):
  ✗ Davis (48% agreement) - papers disagree on detection bias
  ✗ Miller (62% agreement) - mixed assessment of selection bias
  ✗ Taylor (55% agreement) - papers split on attrition bias
  ✗ Anderson (71% agreement) - some disagreement on performance
  ✗ Thomas (69% agreement) - detection bias assessed differently

================================================================================
EXPERIMENT DETAILS:
================================================================================

[1] Green
    Papers assessing: 1
    Papers: 10.3389/falgy.2023.1211949
    
      ✓ selection: high (100% agree)
      ✓ performance: high (100% agree)
      ✓ attrition: low (100% agree)
      ✓ detection: high (100% agree)
      ✓ reporting: high (100% agree)
      ✓ bias_in_conduct: high (100% agree)

[2] Tiffany
    Papers assessing: 1
    Papers: 10.3389/falgy.2023.1211949
    
      ✓ performance: low (100% agree)
      ✓ attrition: low (100% agree)
      ✓ detection: high (100% agree)
      ✓ reporting: high (100% agree)
      ✓ bias_in_conduct: high (100% agree)

[3] Davis
    Papers assessing: 2
    Papers: 10.1038/s41591-023-02123-6, 10.1145/3452383
    
      ✓ selection: low (100% agree)
      ✗ detection: unclear (50% agree) [CONFLICT]
         Values: {unclear: 1, high: 1}
      ✓ performance: high (100% agree)
```

### Output: JSON Report - `processed_export_<timestamp>_experiment_report.json`

**Location:** `paper_pipeline_data/exports/`

**Structure:**
```json
{
  "total_papers": 146,
  "papers_with_rob": 146,
  "total_experiments": 78,
  "summary": {
    "total_experiments_assessed": 78,
    "experiments_with_conflicts": 5,
    "experiments_with_high_agreement": 68
  },
  "experiments": {
    "Green": {
      "paper_count": 1,
      "papers": ["10.3389/falgy.2023.1211949"],
      "domains": {
        "selection": {
          "papers": {
            "10.3389/falgy.2023.1211949": "high"
          },
          "paper_count": 1,
          "consensus_value": "high",
          "agreement_rate": 1.0,
          "value_distribution": {"high": 1},
          "unique_values": ["high"],
          "has_conflict": false
        },
        "detection": {
          "papers": {
            "10.3389/falgy.2023.1211949": "high"
          },
          "paper_count": 1,
          "consensus_value": "high",
          "agreement_rate": 1.0,
          "value_distribution": {"high": 1},
          "unique_values": ["high"],
          "has_conflict": false
        }
      }
    },
    "Davis": {
      "paper_count": 2,
      "papers": ["10.1038/s41591-023-02123-6", "10.1145/3452383"],
      "domains": {
        "selection": {
          "papers": {
            "10.1038/s41591-023-02123-6": "low",
            "10.1145/3452383": "low"
          },
          "paper_count": 2,
          "consensus_value": "low",
          "agreement_rate": 1.0,
          "value_distribution": {"low": 2},
          "unique_values": ["low"],
          "has_conflict": false
        },
        "detection": {
          "papers": {
            "10.1038/s41591-023-02123-6": "unclear",
            "10.1145/3452383": "high"
          },
          "paper_count": 2,
          "consensus_value": "unclear",
          "agreement_rate": 0.5,
          "value_distribution": {"unclear": 1, "high": 1},
          "unique_values": ["unclear", "high"],
          "has_conflict": true
        }
      }
    }
  },
  "conflicting_experiments": ["Davis", "Miller", "Taylor", "Anderson", "Thomas"],
  "high_agreement_experiments": [
    ["Green", 1.0],
    ["Smith", 0.92],
    ["Johnson", 0.88],
    ["Williams", 0.91]
  ]
}
```

### Understanding `paper_count`

**Why is `paper_count = 1` for most experiments?**

This is **expected and normal**. Reasons:

- Each paper in your dataset is a separate systematic review
- Different systematic reviews assess different sets of studies
- The same study name appears in multiple papers only if:
  - Multiple reviews included that specific trial
  - Rare: Same meta-analysis project with multiple papers
  - Very rare: High-impact studies cited across many reviews

**Examples of paper_count interpretation:**

- `paper_count = 1`: Study assessed by 1 paper only (no cross-paper comparison possible)
- `paper_count = 2-3`: Study assessed by 2-3 papers (good basis for conflict detection)
- `paper_count > 5`: Study assessed by multiple papers (strong consensus opportunity)

**Expected distribution:**
- Most experiments: paper_count = 1 (unique to each paper)
- Few experiments: paper_count > 1 (overlap when papers review similar studies)

### How to Find Multi-Paper Experiments

```bash
# Extract experiments appearing in multiple papers
cat processed_export_*_experiment_report.json | \
  jq '.experiments[] | select(.paper_count > 1)'

# Get list of all multi-paper experiments
cat processed_export_*_experiment_report.json | \
  jq '.experiments | to_entries | map(select(.value.paper_count > 1) | .key)'

# Get experiments with conflicts
cat processed_export_*_experiment_report.json | \
  jq '.conflicting_experiments'

# Get high-agreement experiments
cat processed_export_*_experiment_report.json | \
  jq '.high_agreement_experiments'
```

### Interpreting Results

**High Agreement Experiments (>75%):**
- Show consistency across papers in ROB assessment
- Indicate reliable/standard assessment methodology
- Consensus is meaningful when paper_count > 1

**Conflicting Experiments:**
- Papers disagree on ROB assessment for same study
- Possible causes:
  - Different data sources/study years
  - Different assessment criteria applied
  - Data quality issues
  - Genuine disagreement in methodology

**Single-Paper Experiments (paper_count = 1):**
- Cannot be used for cross-paper comparison
- Useful for within-paper consistency checks
- Provides complete RoB profile for a specific review

---

## Quick Test / Example

To test with sample data (no real papers needed):

```bash
cd backend/papers/services
python rob_comparison_example.py
```

Output:
- Console report showing how the analysis works
- JSON file: `rob_comparison_example_report.json`

Example demonstrates:
- 3 papers with ROB assessments
- 4 bias domains (selection, performance, detection, attrition)
- 2 conflicts detected (performance, detection)
- 100% consensus on selection bias (all papers assessed as "low")

---

## Complete Workflow Example

### Step 1: Create DOI File

```bash
cat > my_dois.txt << EOF
10.3389/falgy.2023.1211949
10.1038/s41591-023-02123-6
10.1145/3452383
10.48550/arXiv.2401.12345
10.48550/arXiv.2603.25207
EOF
```

### Step 2: Run Batch Processor

```bash
cd notebooks
python batch_process_dois.py ../data/my_dois.txt
```

**Output:**
```
✅ Loaded 5 DOI(s) from ../data/my_dois.txt

[1/5] Processing: 10.3389/falgy.2023.1211949
  ✅ Success
[2/5] Processing: 10.1038/s41591-023-02123-6
  ✅ Success
[3/5] Processing: 10.1145/3452383
  ✅ Success
[4/5] Processing: 10.48550/arXiv.2401.12345
  ✅ Success
[5/5] Processing: 10.48550/arXiv.2603.25207
  ✅ Success

✅ 5/5 papers processed successfully
✅ Export complete: paper_pipeline_data/exports/processed_export_1234567890.json
```

### Step 3: Check Generated Files

```bash
# All papers with ROB
cat ../paper_pipeline_data/exports/processed_export_1234567890_rob_dois.txt
# Output:
# 10.3389/falgy.2023.1211949
# 10.1038/s41591-023-02123-6
# 10.1145/3452383

# Only OA-extracted papers with ROB (faster re-processing)
cat ../paper_pipeline_data/exports/processed_export_1234567890_rob_oa_only_dois.txt
# Output:
# 10.3389/falgy.2023.1211949
# 10.1038/s41591-023-02123-6
```

### Step 4: Run Cross-Paper Comparison

```bash
cd ../backend/papers/services
python rob_comparison_from_export.py ../../../notebooks/exports/processed_export_1234567890.json
```

**Output:** Console report + `rob_comparison_real_data_report.json`

### Step 5: Run Experiment Analysis

```bash
cd ../../notebooks
python analyze_rob_experiments.py ../paper_pipeline_data/exports/processed_export_1234567890.json
```

**Output:** Console report + `processed_export_1234567890_experiment_report.json`

### Step 6: Explore Results

```bash
# View full JSON structure
cat ../paper_pipeline_data/exports/processed_export_1234567890_experiment_report.json | python -m json.tool | head -100

# Get conflicting experiments
cat ../paper_pipeline_data/exports/processed_export_1234567890_experiment_report.json | jq '.conflicting_experiments'

# Get high-agreement experiments
cat ../paper_pipeline_data/exports/processed_export_1234567890_experiment_report.json | jq '.high_agreement_experiments'

# Find multi-paper experiments
cat ../paper_pipeline_data/exports/processed_export_1234567890_experiment_report.json | \
  jq '.experiments | to_entries | map(select(.value.paper_count > 1)) | length'

# Re-process OA-only papers faster (no Selenium)
cd notebooks
python batch_process_dois.py ../paper_pipeline_data/exports/processed_export_1234567890_rob_oa_only_dois.txt
```

---

## Reference: Bias Domains (RoB2)

From Risk of Bias 2 (Cochrane) assessment tool:

| Domain | Full Name | Meaning |
|--------|-----------|---------|
| **selection** | Bias from randomization process | Quality of random sequence generation and allocation concealment |
| **performance** | Bias due to deviations from intended interventions | Deviations from interventions, baseline imbalance, lack of blinding |
| **detection** | Bias in outcome measurement | Outcome measurement and awareness of intervention assignment |
| **attrition** | Bias due to missing outcome data | Completeness of follow-up, missing data reporting |
| **reporting** | Bias in selection of reported results | Selective outcome reporting, selective analyses |
| **bias_in_conduct** | Overall risk of bias | Synthesis of all domains into overall assessment |

## Reference: Bias Values

Standard ROB assessment values:

- **high**: High risk of bias present
- **low**: Low risk of bias (good quality)
- **unclear**: Cannot determine due to insufficient reporting
- **critical**: Critical risk of bias (severe issues)

---

## File Structure

```
notebooks/
├── batch_process_dois.py              ← Entry point (batch processor)
├── analyze_rob_experiments.py          ← Experiment analysis script
├── to_json.py                          ← Core functions (modified)
└── exports/
    ├── processed_export_<timestamp>.json
    ├── processed_export_<timestamp>_rob_dois.txt
    ├── processed_export_<timestamp>_rob_oa_only_dois.txt
    └── processed_export_<timestamp>_experiment_report.json

backend/papers/services/
├── rob_comparison.py                   ← Core comparison algorithms
├── rob_comparison_by_experiments.py    ← Experiment analysis logic
├── rob_comparison_from_export.py       ← Cross-paper comparison script
├── rob_comparison_example.py           ← Example with sample data
├── rob_extraction.py                   ← ROB detection & extraction
├── ROB_COMPARISON_README.md            ← This file
├── rob_comparison_example_report.json  ← Example output
└── rob_comparison_real_data_report.json ← Real data output (generated)

paper_pipeline_data/
└── exports/
    ├── processed_export_*.json
    └── processed_export_*_experiment_report.json

backend/data/
├── md/                                 ← Extracted markdown files
├── html/                               ← HTML snapshots
├── pdf/                                ← Downloaded PDFs
└── png/                                ← Extracted figures

COMPLETE_WORKFLOW_GUIDE.md             ← Comprehensive workflow guide (generated)
IMPLEMENTATION_SUMMARY.md              ← Summary of recent changes
```

---

## Performance Benchmarks

### Extraction Speed

**Per paper:**
- OA API: 5-15 seconds (preferred)
- Selenium: 20-40 seconds (fallback)
- Concurrent processing: 4 papers at a time

**Per dataset:**
- 10 papers: 2-5 minutes
- 100 papers: 20-50 minutes
- 1000 papers: 3-8 hours

### Storage Requirements

**Per paper:**
- Markdown: 10-50 KB
- Images: 100 KB - 2 MB
- JSON export: 1-5 KB
- **Total per paper: 0.5-5 MB** (depends on content richness)

**Batch sizes:**
- 10 papers: 5-50 MB
- 100 papers: 50-500 MB
- 1000 papers: 500 MB - 5 GB

### Memory Usage

- Batch processor: 200-500 MB (relatively stable)
- Export processing: 1-2 GB (for large datasets)
- Analysis scripts: 500 MB - 1 GB

---

## Troubleshooting

### Problem: "No papers were successfully processed"

**Possible causes:**
- Invalid DOI format
- Network connectivity issues
- Papers not in PMC or arXiv
- API rate limiting

**Solutions:**
1. Test with known good DOI: `10.3389/falgy.2023.1211949`
2. Check internet connection
3. Verify DOI format (should start with "10.")
4. Wait a few minutes and retry (API rate limit)

### Problem: "No ROB artifacts found"

**Possible causes:**
- Paper doesn't contain ROB assessment
- ROB table in unexpected format
- ROB extraction failed

**Solutions:**
1. Check console output for extraction details
2. Manually inspect the markdown file to verify ROB content
3. Check if paper is a systematic review/meta-analysis

### Problem: Memory/disk space exceeded

**For large datasets (>1000 papers):**
```bash
# Split into smaller batches
split -l 100 large_dois.txt dois_batch_
python batch_process_dois.py dois_batch_aa
python batch_process_dois.py dois_batch_ab

# Combine results manually or use separate analysis runs
```

### Problem: Extraction method tracking missing

**If `extraction_method` field is None:**
1. Verify `to_json.py` is updated with changes
2. Re-run batch processor to regenerate export
3. Check that download_pmc_images() returns 3-tuple

### Problem: JSON parsing error

**If report files don't load:**
```bash
# Validate JSON syntax
python -m json.tool processed_export_*.json > /dev/null

# If invalid, check for incomplete writes or truncation
ls -lh processed_export_*.json
```

---

## Advanced Usage

### Filtering Results by Extraction Method

```bash
# Get papers extracted via OA API with ROB
cat processed_export_*.json | jq '.[] | select(.extraction_method == "oa_api" and .rob_artifacts != null) | .paper_id'

# Get papers needing Selenium that have ROB
cat processed_export_*.json | jq '.[] | select(.extraction_method == "selenium" and .rob_artifacts != null) | .paper_id'
```

### Analyzing Specific Bias Domains

```bash
# Get all papers assessing selection bias
cat rob_comparison_real_data_report.json | jq '.table_alignment.domain_matrix.selection'

# Get papers with conflicting assessments on detection bias
cat rob_comparison_real_data_report.json | jq '.table_alignment.conflicts[] | select(.bias_domain == "detection")'
```

### Finding Experiments with Specific Characteristics

```bash
# Experiments appearing in exactly 2 papers
cat processed_export_*_experiment_report.json | \
  jq '.experiments | to_entries | map(select(.value.paper_count == 2)) | .[].key'

# Experiments with <50% agreement
cat processed_export_*_experiment_report.json | \
  jq '.experiments[] | select(any(.domains[]; .agreement_rate < 0.5))'
```

### Batch Processing with Error Recovery

```bash
# If interrupted, rerun with full list - already processed papers are skipped
# To force reprocessing:
rm backend/data/md/PMC_ID.md  # Delete specific paper
python batch_process_dois.py my_dois.txt  # Rerun
```

---

## Tips & Best Practices

1. **Start small:** Test with 5-10 papers first to verify setup
2. **Monitor progress:** Watch console output for errors/patterns
3. **Cache results:** Keep export JSON for multiple analyses
4. **Separate concerns:** Use OA-only list for fastest re-processing
5. **Verify manually:** Always spot-check extracted ROB data
6. **Track metadata:** Note extraction method for reproducibility
7. **Use jq for filtering:** Easy JSON manipulation without custom scripts

---

## References

- **Cochrane Risk of Bias 2 Tool:** https://www.riskofbiastool.info/
- **RoB2 User Guide:** https://www.riskofbiastool.info/welcome/o8gtx
- **PubMed Central OA API:** https://www.ncbi.nlm.nih.gov/pmc/
- **arXiv API:** https://arxiv.org/help/api
