# Phase 2 Implementation - Quick Reference

## ✅ What Was Done

**Objective:** Create a report system to easily see ROB tables with quick links to PDFs and markdown files for comparison.

### Code Changes (to_json.py)
1. ✅ `extract_images_from_oa()` - Now extracts PDF from OA tar.gz
2. ✅ `download_pmc_images()` - Returns 4-tuple with pdf_path
3. ✅ `process_pmc()` - Stores pdf_path in metadata
4. ✅ `export_rob_tables_for_inspection()` - NEW export for inspection-friendly format

### Batch Processor Update
- ✅ `batch_process_dois.py` - Now calls new export function automatically

### New Inspection Notebook
- ✅ `inspect_rob_tables_report.ipynb` - Beautiful HTML report with tables and file links

---

## 🚀 How to Use

### 1. Process Your Papers
```bash
cd /home/jgrzyb/Documents/Python/ai4es-oa-paper-scrapper/notebooks
python batch_process_dois.py ../data/dois_test.txt
```

**Output includes:**
- `rob_tables_inspection_<timestamp>.json` ← This has the ROB tables!
- PDF files extracted from OA API
- Markdown files with sections and tables

### 2. Open the Inspection Report
```bash
jupyter notebook inspect_rob_tables_report.ipynb
```

**The notebook will:**
- Load the ROB tables export
- Show all papers with links to PDF and markdown
- Detect conflicts (different papers assessing same experiment differently)
- Generate HTML report you can save/share

---

## 📊 What You'll See

### Paper Index Table
| DOI | N_Tables | Method | MD_Path | PDF_Path |
|-----|----------|--------|---------|----------|
| 10.1038/s41591-023-02... | 3 | oa_api | paper_pipeline_data/md/PMC123456.md | paper_pipeline_data/pdf/PMC123456.pdf |

### Conflict Detection
```
⚠️  Study "Davis" has conflicting assessments:
    Domain: detection
    Paper 1 says: "high"
    Paper 2 says: "unclear"
    
    📄 Paper 1: paper_pipeline_data/md/PMC111111.md
    📕 Paper 1 PDF: paper_pipeline_data/pdf/PMC111111.pdf
    
    📄 Paper 2: paper_pipeline_data/md/PMC222222.md
    📕 Paper 2 PDF: paper_pipeline_data/pdf/PMC222222.pdf
```

### Side-by-Side Comparison
```
Experiment: Davis
Papers assessing: 2

| DOI | Randomization | Deviations | Missing Data |
|-----|---|---|---|
| 10.1038/s41591... | Low | High | Low |
| 10.1145/3452... | Low | High | Unclear ← CONFLICT! |
```

---

## 📁 Output Files

After running the batch processor:

```
paper_pipeline_data/
├── md/
│   ├── PMC123456.md      ← Markdown with ROB tables
│   └── PMC654321.md
├── pdf/
│   ├── PMC123456.pdf     ← PDF from OA API extraction
│   └── PMC654321.pdf
└── exports/
    ├── processed_export_1234567890.json        (main export)
    ├── rob_tables_inspection_1234567890.json   (NEW - for inspection)
    ├── rob_tables_report_1234567890.html       (HTML report)
    └── *_rob_dois.txt                          (DOI lists)
```

---

## 💡 Key Features

### ✓ PDF Extraction
- Automatically extracts PDFs from OA API tar.gz
- Stored in `paper_pipeline_data/pdf/`
- Paths included in report for easy access

### ✓ ROB Table Export
- Extracts raw table data (headers + rows)
- No normalization applied yet
- Perfect for manual inspection before analysis

### ✓ Conflict Detection
- Finds when multiple papers assess the same experiment
- Shows disagreements in ROB values
- Highlights which papers disagree

### ✓ Quick Links
- Direct file paths to markdown and PDF
- Copy-paste ready for verification
- Easy side-by-side comparison

### ✓ HTML Report
- Professional report with all findings
- Can be printed or shared
- Summarizes conflicts and statistics

---

## 🔍 Example Workflow

### Find a Conflict
1. Open `inspect_rob_tables_report.ipynb`
2. Run Cell 4 (Conflict Detection) - see all conflicts
3. See example: "Study Davis has different values in 2 papers"

### Investigate the Conflict
1. Click links to markdown files
2. Find the ROB table in the markdown
3. See the raw table data (before normalization)
4. Open the PDF to verify visually

### Example Command
```python
# In notebook, after running cells:
show_experiment_with_links('Davis')
```

Outputs:
```
EXPERIMENT: Davis
Papers assessing: 2

Assessment values side-by-side:
- Paper 1: Detection = high
- Paper 2: Detection = unclear

FILE LINKS:
📄 Paper 1: paper_pipeline_data/md/PMC111111.md
📕 Paper 1: paper_pipeline_data/pdf/PMC111111.pdf
📄 Paper 2: paper_pipeline_data/md/PMC222222.md
📕 Paper 2: paper_pipeline_data/pdf/PMC222222.pdf
```

---

## 📋 Checking if Implementation Works

### Verify Files Exist
```bash
cd notebooks
ls inspect_rob_tables_report.ipynb
cat to_json.py | grep "def export_rob_tables_for_inspection"
cat batch_process_dois.py | grep "export_rob_tables_for_inspection"
```

### Test with Small Batch
```bash
# Process just 1-2 test papers
python batch_process_dois.py ../data/dois_test.txt

# Check if new export file created
ls paper_pipeline_data/exports/rob_tables_inspection_*.json
```

### Open Notebook and Run Cells
1. Jupyter → `inspect_rob_tables_report.ipynb`
2. Run Cell 2 (Load ROB Tables Export) - should load latest file
3. Run Cell 4 (Build Paper Index) - should show papers with PDF/MD paths
4. Run Cell 6 (Conflict Detection) - should show any conflicts found

---

## 🎯 Now You Have Evidence!

Your report will show:
- ✅ How many papers have conflicting ROB assessments
- ✅ Which experiments are affected
- ✅ Which bias domains conflict
- ✅ Side-by-side values that differ
- ✅ Direct links to PDF/markdown for manual verification

**This answers your question:** "Do ROB values compare consistently across papers?" 
→ If conflicts exist, the answer is NO - with evidence!

---

## 📞 Next Actions

1. **Process your main dataset:**
   ```bash
   python batch_process_dois.py /path/to/your/dois.txt
   ```

2. **Generate the report:**
   ```bash
   jupyter notebook inspect_rob_tables_report.ipynb
   # Run all cells - generates rob_tables_report_*.html
   ```

3. **Review findings:**
   - Open the HTML report in a browser
   - Check which experiments conflict
   - Click markdown/PDF links to verify manually

4. **Document patterns:**
   - Are conflicts from different RoB tools?
   - Different row naming conventions?
   - Genuine measurement disagreement?
   - Use this to inform your analysis approach

---

**Implementation complete! Ready to inspect your ROB tables.** ✅
