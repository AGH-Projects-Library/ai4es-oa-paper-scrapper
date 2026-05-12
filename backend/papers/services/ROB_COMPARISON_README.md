# ROB Comparison Scripts - Usage Guide

## Overview

Three scripts for Risk of Bias (ROB) comparison and analysis:

1. **`rob_comparison.py`** - Core module with comparison algorithms (import this)
2. **`rob_comparison_example.py`** - Example with sample data
3. **`rob_comparison_from_export.py`** - Real data from `to_json.py` export

## Workflow

### Step 1: Generate Data with `to_json.py`

Run your scraper with your DOI dataset:

```bash
cd notebooks
python to_json.py < your_dois.txt
```

This generates a JSON export file (e.g., `processed_export_1234567890.json`) in `notebooks/exports/`

### Step 2: Run ROB Comparison on Real Data

```bash
cd backend/papers/services
python rob_comparison_from_export.py ../../../notebooks/exports/processed_export_1234567890.json
```

Output:
- Console report with insights (conflicts, consensus, recommendations)
- JSON file: `rob_comparison_real_data_report.json` (full data)

## Quick Test / Example

To test with sample data (no real papers needed):

```bash
cd backend/papers/services
python rob_comparison_example.py
```

Output:
- Console report showing how the analysis works
- JSON file: `rob_comparison_example_report.json`

## What Gets Generated

### Console Output

Shows:
- **Summary**: Total papers, artifacts, breakdown by type
- **Bias Domain Alignment**: Matrix of bias domains × papers
- **Consensus**: Majority voting results with agreement rates
- **Conflicts**: Where papers disagree on bias scores
- **Popular Sections**: Most common ROB assessment sections
- **Recommendations**: Automated insights

### JSON Report

Full data structure:
```json
{
  "summary": {
    "num_papers": 5,
    "total_artifacts": 42,
    "total_text_artifacts": 5,
    "total_table_artifacts": 35,
    "total_ocr_artifacts": 2
  },
  "table_alignment": {
    "domain_matrix": { "selection": { "PMC001": "low", ... }, ... },
    "conflicts": [ { "bias_domain": "performance", "unique_values": ["low", "high"], ... }, ... ],
    "coverage": { "selection": 5, "performance": 4, ... },
    "summary": { "selection": { "consensus_value": "low", "agreement_rate": 0.95 }, ... }
  },
  "section_artifacts": {
    "by_section": { "Assessment of risk of bias": [ ... ], ... },
    "popular_sections": [ ["Assessment of risk of bias", 4], ... ],
    "paper_section_coverage": { "PMC001": ["Assessment of risk of bias"], ... }
  },
  "ocr_artifacts": {
    "by_paper": { "PMC001": [ { "section": "...", "method": "ocr_table", "confidence": 0.75 }, ... ] },
    "total_ocr_artifacts": 2,
    "average_confidence": 0.75,
    "methods_used": { "ocr_table": 2 }
  },
  "recommendations": [
    {
      "type": "investigate_conflicts",
      "message": "Found 1 bias domain with conflicting assessments...",
      "conflicts": 1
    },
    ...
  ]
}
```

## Understanding Results

### Consensus & Agreement

- **Consensus**: Most common bias value (low/high/unclear) across papers
- **Agreement Rate**: Percentage of papers that agree on consensus value
  - 100% = all papers agree
  - 50% = split opinion (useful for identifying methodology differences)

### Conflicts

Detected when papers assess the same bias domain differently. Indicates:
- Different methodologies used
- Different inclusion criteria
- Potential quality differences in papers

### Recommendations

Automatically generated insights:
- **investigate_conflicts**: Review methodological differences
- **high_confidence_ocr**: OCR results are reliable
- **review_low_confidence**: Manual review needed for OCR
- **improve_coverage**: Some papers lack explicit ROB assessments

## File Structure

```
backend/papers/services/
├── rob_comparison.py                    # Core module (import this)
├── rob_comparison_example.py            # Example with sample data
├── rob_comparison_from_export.py        # Real data analyzer
├── rob_extraction.py                    # ROB text/table/image extraction
├── rob_comparison_example_report.json   # Example output
└── rob_comparison_real_data_report.json # Real data output (generated)

notebooks/
├── to_json.py                           # Scraper (generates export)
└── exports/
    └── processed_export_*.json          # Input for rob_comparison_from_export.py
```

## Tips

1. **Large Datasets**: If comparing many papers, the JSON report will be large. Filter by `papers_data` before calling `generate_comparison_report()`.

2. **Low Coverage**: If some domains appear in few papers, it might indicate:
   - Those papers used different assessment tools
   - Those domains weren't relevant for all studies

3. **Consensus ≠ Truth**: Majority voting shows agreement, not correctness. Always verify conflicts manually.

4. **OCR Quality**: If OCR confidence < 0.7, manually review the extracted text before using it.

## Example Data

`rob_comparison_example.py` demonstrates:
- 3 papers with ROB assessments
- 4 bias domains (selection, performance, detection, attrition)
- 2 conflicts detected (performance, detection)
- 100% consensus on selection bias (all papers assessed as "low")
