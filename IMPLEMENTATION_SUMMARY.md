# ROB Analysis Implementation Summary

## Changes Made

### 1. Enhanced Export Function (to_json.py)

**Modified `download_pmc_images()` function:**
- Now returns extraction method as third value: `(local_paths, html_path, extraction_method)`
- Returns `"oa_api"` if extraction succeeded via OA API
- Returns `"selenium"` if extraction fell back to Selenium rendering

**Updated `process_pmc()` function:**
- Captures extraction method and stores it in metadata
- Changed source from `"pmc"` to `"pubmed"` for consistency with standard terminology

**Simplified `export_all_processed_json()` output:**
- Creates `processed_export_XXXXX_rob_dois.txt`:
  - Contains ONLY DOIs of papers with ROB artifacts
  - One DOI per line (no additional info)
  - Suitable for piping to next processing stage

- Creates `processed_export_XXXXX_rob_oa_only_dois.txt`:
  - Contains ONLY DOIs of papers extracted via OA API WITH ROB artifacts
  - These papers don't require Selenium (fast extraction)
  - Perfect for re-processing without browser overhead

### 2. Experiment-Focused ROB Comparison (rob_comparison_by_experiments.py)

**New analysis module that:**
- Extracts study names from ROB tables (column 0 = row labels/experiment names)
- Groups ROB assessments by experiment across papers
- Generates structured report with:
  - Each unique experiment with papers that assessed it
  - ROB grades for each bias domain within each experiment
  - Consensus values and agreement rates
  - Conflict detection (disagreements across papers)

**Report Structure:**
```
Experiment: Study Name X
  Papers assessing: 5
  Papers: [DOI1, DOI2, DOI3, DOI4, DOI5]
  
  Bias Domain: selection
    Consensus: high
    Agreement: 80% (4/5 papers agree)
    Distribution: {high: 4, low: 1}
  
  Bias Domain: detection
    Consensus: unclear
    Agreement: 60% (3/5 papers agree)
    Distribution: {unclear: 3, high: 2} [CONFLICT]
```

### 3. Command-Line Analysis Tool (analyze_rob_experiments.py)

**Usage:**
```bash
python analyze_rob_experiments.py path/to/processed_export_XXXXX.json
```

**Generates:**
1. Console output with:
   - Overall statistics
   - List of high-agreement experiments (>75% consensus)
   - List of conflicting experiments
   - Detailed breakdown of first 30 experiments

2. JSON report file: `processed_export_XXXXX_experiment_report.json`
   - Full structured data for all experiments
   - Suitable for further analysis/visualization
   - Contains conflict information and agreement rates

## Workflow Example

```bash
# 1. Run scraping and export
cd notebooks
python batch_process_dois.py my_dois.txt

# 2. Analyze ROB data by experiments
python analyze_rob_experiments.py ../paper_pipeline_data/exports/processed_export_1234567.json

# 3. Extract DOIs for re-processing (no Selenium)
cat ../paper_pipeline_data/exports/processed_export_1234567_rob_oa_only_dois.txt > dois_for_faster_reprocessing.txt
```

## Key Outputs

### `_rob_dois.txt`
- Simple list of all papers with ROB artifacts
- Format: One DOI per line
- Use case: Track which papers contain ROB data

### `_rob_oa_only_dois.txt`  
- Only papers extracted via fast OA API (no Selenium)
- Format: One DOI per line
- Use case: Identify papers that don't need browser rendering

### `_experiment_report.json`
- Full structured analysis by experiment
- Includes consensus values, agreement rates, conflicts
- Use case: Detailed analysis, visualization, further processing

## Key Insights from Report

**High Agreement Experiments:**
- Show consistency across papers in how they assess specific studies
- Indicate reliable/standard assessment methodology
- Values >75% agreement are meaningful

**Conflicting Experiments:**
- Papers disagree on ROB assessment for same experiment
- May indicate:
  - Different data sources/years
  - Different assessment criteria
  - Data quality issues
  - Genuine disagreement in methodology

**Paper Count per Experiment:**
- Shows how many papers assessed a particular experiment
- Higher count = more confidence in consensus value
- Lower count (<2) may not be statistically meaningful
