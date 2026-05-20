import os
import json
from typing import List
from .models import DocumentInfo

def export_documents(docs: List[DocumentInfo], output_path: str):
    """
    Exports a list of DocumentInfo models to a single JSON file.
    
    Args:
        docs: List of DocumentInfo objects to export
        output_path: Full file path for the output JSON (e.g., "exports/processed_export_123456.json")
    """
    # Ensure the directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    data = [doc.to_dict() for doc in docs]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"[EXPORT] Successfully saved {len(docs)} documents to {output_path}")
