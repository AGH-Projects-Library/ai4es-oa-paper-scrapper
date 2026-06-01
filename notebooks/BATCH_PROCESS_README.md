# Batch Process DOIs - Usage Guide

## Problem Solved

The original `to_json.py` script has interactive prompts that don't work with stdin redirection:

```bash
# ❌ This doesn't work - causes EOFError
python to_json.py < my_dois.txt
```

The new `batch_process_dois.py` script fixes this with a non-interactive batch processor.

## Usage

```bash
cd notebooks
python batch_process_dois.py <path_to_dois_file>
```

### Examples

**Using the test file:**
```bash
python batch_process_dois.py ../data/dois_test.txt
```

**Using your own DOI file:**
```bash
python batch_process_dois.py /path/to/my_dois.txt
```

## Input File Format

Text file with one DOI per line:
```
10.48550/arXiv.2603.24132
10.48550/arXiv.2603.25207
10.1145/3452383
# This is a comment (ignored)

# Empty lines above are ignored
10.1101/2023.01.01.100001
```

Features:
- ✅ One DOI per line
- ✅ Comments starting with `#` are ignored
- ✅ Empty lines are ignored
- ✅ Works with relative or absolute paths

## Output

### Console Output
- Progress: `[1/51] Processing: 10.48550/arXiv.2603.24132`
- Status: `✅ Success` or `❌ Error: <message>`
- Summary at end with success/failure counts

### Generated Files
- Processed papers: `backend/data/md/`, `backend/data/pdf/`, etc.
- **JSON Export**: `notebooks/exports/processed_export_*.json` (main output)

## Complete Workflow

```bash
# 1. Process your DOIs
cd notebooks
python batch_process_dois.py my_dois.txt

# 2. When done, it tells you where the export is saved
# Output: "✅ Export complete: notebooks/exports/processed_export_1234567890.json"

# 3. Analyze with ROB comparison
cd ../backend/papers/services
python rob_comparison_from_export.py ../../../notebooks/exports/processed_export_1234567890.json

# 4. Get cross-paper ROB analysis
# Outputs: Console report + rob_comparison_real_data_report.json
```

## Script Features

| Feature | Details |
|---------|---------|
| **Non-interactive** | No prompts - fully automated |
| **Batch processing** | Handles all DOIs in one run |
| **Progress tracking** | Shows `[N/total]` for each DOI |
| **Error handling** | Continues on errors, reports summary |
| **Auto-export** | Exports JSON when done (ready for ROB analysis) |
| **Interrupt support** | Press Ctrl+C to stop gracefully |
| **Comments & whitespace** | Ignores `#` comments and empty lines |

## Troubleshooting

### Error: File not found
```
❌ Error: File not found: my_dois.txt
```
**Solution**: Use correct path (relative or absolute)
```bash
python batch_process_dois.py ../data/dois_test.txt
```

### Error: No DOIs to process
```
❌ No DOIs to process
```
**Solution**: Check that file contains actual DOIs, not just comments/empty lines

### Error: No papers were successfully processed
```
❌ No papers were successfully processed
```
**Solution**: Check DOI format and internet connectivity. Review individual error messages.

### Script hangs
- It's normal for each DOI to take 10-30 seconds
- Press Ctrl+C to stop
- Already processed papers are not lost, check `backend/data/` and `notebooks/exports/`

## Tips

1. **Test first**: Use `../data/dois_test.txt` to test the setup
2. **Monitor progress**: Watch the console to see which DOIs are failing
3. **Partial runs**: If interrupted, already processed papers are saved. Rerun with full list to continue.
4. **Check export size**: Large exports (1000+ papers) may take time to process. Start small.

## See Also

- [ROB Comparison Guide](../backend/papers/services/ROB_COMPARISON_README.md)
- [to_json.py](to_json.py) - Original interactive script (for reference)
- [batch_process_dois.py](batch_process_dois.py) - This batch processor
