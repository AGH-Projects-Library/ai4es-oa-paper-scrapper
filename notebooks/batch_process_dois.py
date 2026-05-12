#!/usr/bin/env python3
"""
Batch Process DOIs using to_json.py functions

Non-interactive script that processes a list of DOIs and generates JSON export.

Usage:
    python batch_process_dois.py <path_to_dois_file>

Example:
    python batch_process_dois.py ../data/dois_test.txt
    python batch_process_dois.py /path/to/my_dois.txt

Input file format:
    - One DOI per line
    - Lines starting with # are ignored (comments)
    - Empty lines are ignored

Output:
    - Processed data: backend/data/md/, backend/data/pdf/, etc.
    - Export JSON: notebooks/exports/processed_export_*.json
"""

import sys
import os
import json
import time
from pathlib import Path

# Add to_json to path to import its functions
sys.path.insert(0, os.path.dirname(__file__))


try:
    from to_json import (
        process_arxiv, process_pmc, process_document,
        export_all_processed_json, is_arxiv_identifier
    )
except ImportError as e:
    print(f"❌ Error: Could not import from to_json.py: {e}")
    sys.exit(1)

def read_dois_from_file(filepath):
    """
    Read DOIs from a text file.
    
    Args:
        filepath: Path to file with DOIs (one per line)
    
    Returns:
        List of valid DOIs
    """
    if not os.path.exists(filepath):
        print(f"❌ Error: File not found: {filepath}")
        return []
    
    dois = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                dois.append(line)
        
        print(f"✅ Loaded {len(dois)} DOI(s) from {filepath}")
        return dois
    
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []


def process_doi_batch(dois, verbose=True):
    """
    Process a batch of DOIs.
    
    Args:
        dois: List of DOI strings
        verbose: Print progress
    
    Returns:
        List of processed paper data
    """
    processed = []
    failed = []
    
    for i, doi in enumerate(dois, 1):
        print(f"\n[{i}/{len(dois)}] Processing: {doi}")
        
            
        try:
            # Route to arxiv or PMC using process_document router
            result = process_document(doi)
            if result:
                processed.append(result)
                print(f"  ✅ Success")
            else:
                print(f"  ⚠️  Could not process")
                failed.append((doi, "Processing returned None"))
        
        except KeyboardInterrupt:
            print(f"\n⏸️  Interrupted by user")
            break
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append((doi, str(e)))
    
    # Summary
    print("\n" + "=" * 80)
    print(f"BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Successfully processed: {len(processed)}/{len(dois)}")
    
    if failed:
        print(f"Failed: {len(failed)}")
        for doi, error in failed:
            print(f"  - {doi}: {error}")
    
    return processed, failed


def main():
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python batch_process_dois.py <path_to_dois_file>")
        print("\nExample:")
        print("  python batch_process_dois.py ../data/dois_test.txt")
        print("  python batch_process_dois.py /path/to/my_dois.txt")
        print("\nInput file format:")
        print("  - One DOI per line")
        print("  - Lines starting with # are ignored (comments)")
        print("  - Empty lines are ignored")
        sys.exit(1)
    
    dois_file = sys.argv[1]
    
    print("=" * 80)
    print("BATCH DOI PROCESSOR")
    print("=" * 80)
    
    # Read DOIs
    dois = read_dois_from_file(dois_file)
    if not dois:
        print("❌ No DOIs to process")
        sys.exit(1)
    
    # Process in batch
    processed, failed = process_doi_batch(dois, verbose=True)
    
    if not processed:
        print("\n❌ No papers were successfully processed")
        sys.exit(1)
    
    # Export results
    print(f"\n📤 Exporting {len(processed)} papers to JSON...")
    try:
        export_path = export_all_processed_json(processed)
        print(f"✅ Export complete: {export_path}")
    except Exception as e:
        print(f"❌ Export failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
    print(f"\nNext step: Run ROB comparison on the export")
    print(f"  cd backend/papers/services")
    print(f"  python rob_comparison_from_export.py {export_path}")
    print()


if __name__ == '__main__':
    main()
