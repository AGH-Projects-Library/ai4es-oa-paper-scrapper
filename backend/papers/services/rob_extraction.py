import re
from typing import Any
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    HAS_OCR_DEPS = True
except ImportError:
    HAS_OCR_DEPS = False



# Standard ROB bias domains (ROBINS-I + RoB 2 frameworks)
ROB_DOMAINS = {
    "selection": r"\b(selection|inclusion|eligibility)\s+(bias|criteria|bias)\b",
    "performance": r"\b(performance|treatment|intervention)\s+bias\b",
    "detection": r"\b(detection|measurement|outcome|assessor)\s+bias\b",
    "attrition": r"\b(attrition|loss\s+to\s+follow[\s-]*up|dropout)\s+bias\b",
    "reporting": r"\b(reporting|publication|selective\s+reporting)\s+bias\b",
    "bias_in_conduct": r"\b(bias\s+in\s+conduct|methodological\s+quality|risk\s+of\s+bias)\b",
    "overall": r"\b(overall|summary)\s+(risk\s+of\s+)?bias\b",
}

# Standard ROB assessment values (Low/High/Unclear or numeric scales)
ROB_VALUES = [
    "low", "high", "unclear", "some concerns", "critical",
    "1", "2", "3", "4", "5",
    "yes", "no", "partial", "na", "n/a",
]

ROB_PATTERNS = [
    re.compile(r"\brisk\s*[- ]?of\s*[- ]?bias\b", re.IGNORECASE),
    re.compile(r"\brob2\b", re.IGNORECASE),
    re.compile(r"\brobins\s*[- ]?i\b", re.IGNORECASE),
    re.compile(r"\bbias\s+assessment\b", re.IGNORECASE),
    re.compile(r"\bbias\s+domain\b", re.IGNORECASE),
    re.compile(r"\bselection\s+bias\b", re.IGNORECASE),
    re.compile(r"\bperformance\s+bias\b", re.IGNORECASE),
    re.compile(r"\bdetection\s+bias\b", re.IGNORECASE),
    re.compile(r"\battrition\s+bias\b", re.IGNORECASE),
    re.compile(r"\breporting\s+bias\b", re.IGNORECASE),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def text_contains_rob(text: str) -> bool:
    text = text or ""
    return any(pattern.search(text) for pattern in ROB_PATTERNS)


def parse_markdown_table_block(lines: list[str]) -> dict[str, Any] | None:
    if len(lines) < 2:
        return None

    def split_row(line: str) -> list[str]:
        cells = [cell.strip() for cell in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    rows = [split_row(line) for line in lines]
    header = rows[0]
    data_rows = []

    for row in rows[1:]:
        if all(re.fullmatch(r"[-: ]+", cell or "") for cell in row):
            continue

        if len(row) < len(header):
            row += [""] * (len(header) - len(row))
        elif len(row) > len(header):
            row = row[: len(header)]

        data_rows.append(row)

    markdown = "\n".join(lines)
    return {
        "header": header,
        "rows": data_rows,
        "markdown": markdown,
    }


def iter_markdown_blocks(md_text: str):
    current_section = None
    current_lines = []
    pending_table = []

    def flush_table():
        nonlocal pending_table
        if pending_table:
            yield {"type": "table", "lines": pending_table.copy(), "section": current_section}
            pending_table = []

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("#"):
            if pending_table:
                yield from flush_table()
            if current_lines:
                yield {"type": "section", "heading": current_section, "lines": current_lines.copy()}
            heading = re.sub(r"^#+\s*", "", stripped)
            current_section = heading
            current_lines = []
            continue

        if stripped.startswith("|"):
            pending_table.append(stripped)
            continue

        if pending_table:
            yield from flush_table()

        if stripped:
            current_lines.append(stripped)

    if pending_table:
        yield from flush_table()

    if current_lines:
        yield {"type": "section", "heading": current_section, "lines": current_lines.copy()}


def extract_rob_from_images(local_images: list[dict[str, Any]], section: str | None = None, paper_id: str | None = None, confidence_threshold: float = 0.7) -> list[dict[str, Any]]:
    """
    Extract ROB information from images using OCR fallback.
    
    Args:
        local_images: List of {path, caption, placeholder} dicts
        section: Section name where images appear
        paper_id: Paper identifier
        confidence_threshold: Minimum confidence to include OCR result
    
    Returns:
        List of {artifact_type: 'ocr_table', method, confidence, text, ...} records.
    """
    if not HAS_OCR_DEPS or not local_images:
        return []
    
    artifacts = []
    
    for image_data in local_images:
        image_path = image_data.get("path")
        caption = image_data.get("caption", "")
        placeholder = image_data.get("placeholder", "")
        
        # Check if image is likely a ROB figure
        if not text_contains_rob(caption) and not text_contains_rob(placeholder):
            continue
        
        # Try to read the image file
        try:
            # Try absolute path first, then relative from paper_pipeline_data
            if not Path(image_path).exists():
                # Try to construct alternative paths
                alt_paths = [
                    Path("/home/jgrzyb/Documents/Python/ai4es-oa-paper-scrapper") / image_path,
                    Path("/home/jgrzyb/Documents/Python/ai4es-oa-paper-scrapper/paper_pipeline_data") / image_path,
                ]
                image_path = next((p for p in alt_paths if p.exists()), image_path)
            
            if not Path(image_path).exists():
                continue
            
            img = Image.open(image_path)
            
            # Try table-focused OCR first (--psm 6: uniform block of text)
            try:
                table_text = pytesseract.image_to_string(img, config='--psm 6')
                method = 'ocr_table'
                confidence = 0.75
            except Exception:
                # Fall back to full-page OCR (--psm 3)
                try:
                    table_text = pytesseract.image_to_string(img, config='--psm 3')
                    method = 'ocr_full'
                    confidence = 0.65
                except Exception:
                    continue
            
            # Normalize extracted text
            extracted_text = normalize(table_text)
            
            if extracted_text and len(extracted_text) > 10:  # Only include non-trivial text
                artifacts.append({
                    "artifact_type": "ocr_table",
                    "paper_id": paper_id,
                    "section": section,
                    "image_path": str(image_path),
                    "caption": caption,
                    "method": method,
                    "confidence": confidence,
                    "text": extracted_text[:500],  # Truncate to 500 chars
                    "full_text": extracted_text,
                })
        
        except Exception as e:
            # Log error but continue with next image
            continue
    
    return artifacts


def extract_rob_artifacts_from_markdown(md_text: str, paper_id: str | None = None) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    current_section = None

    for block in iter_markdown_blocks(md_text):
        if block["type"] == "section":
            current_section = block.get("heading")
            section_text = normalize(" ".join(block.get("lines", [])))

            if text_contains_rob(current_section or "") or text_contains_rob(section_text):
                artifacts.append({
                    "artifact_type": "section",
                    "paper_id": paper_id,
                    "section": current_section,
                    "match": current_section if text_contains_rob(current_section or "") else section_text,
                    "confidence": 0.92,
                    "text": section_text,
                })

        elif block["type"] == "table":
            table = parse_markdown_table_block(block.get("lines", []))
            if not table:
                continue

            table_text = table["markdown"]
            header_text = " ".join(table.get("header") or [])
            rows_text = " ".join(" ".join(row) for row in table.get("rows") or [])
            combined_text = normalize(" ".join([header_text, rows_text, table_text]))

            if text_contains_rob(header_text) or text_contains_rob(combined_text):
                artifact = {
                    "artifact_type": "table",
                    "paper_id": paper_id,
                    "section": current_section,
                    "match": header_text if text_contains_rob(header_text) else combined_text,
                    "confidence": 0.97,
                    "table": table,
                }
                
                # Try to normalize ROB table schema
                normalized_records = normalize_rob_table(table, current_section)
                if normalized_records:
                    artifact["normalized_records"] = normalized_records
                
                artifacts.append(artifact)

    return artifacts


def extract_bias_domain_from_header(header_text: str) -> str | None:
    """
    Extract bias domain from RoB 2 style headers.
    E.g., "Risk of bias from randomization process" → "selection"
    """
    header_lower = header_text.lower()
    
    # For RoB 2 style headers, extract the domain concept from the header FIRST
    # E.g., "Risk of bias from randomization process" → look for "randomization"
    # This must be checked BEFORE the generic domain patterns
    # Note: Use ? to handle singular/plural, use .* for flexible word matching
    # ORDER MATTERS: Check specific/longer patterns first to avoid false matches
    rob2_patterns = [
        ("attrition", r"\b(missing|loss\s+to\s+follow|attritions?|dropouts?|follow[\s-]*up)\b.*\bdata\b"),
        ("attrition", r"\b(missing|loss\s+to\s+follow|attritions?|dropouts?|follow[\s-]*up)\b"),
        ("reporting", r"\b(selection|selective)\b.*\b(results?|report|publication)\b"),
        ("reporting", r"\b(reportings?|selective\s+reportings?|publications?|published)\b"),
        ("performance", r"\b(deviations?|intended\s+interventions?|performance|treatments?|exposures?)\b"),
        ("detection", r"\b(measurements?|assessors?|blindings?|maskings?|knowledge)\b"),
        ("selection", r"\b(randomiza?tions?|random\s+allocations?|allocations?|sequencings?|inclusions?|eligibilities?)\b"),
    ]
    
    for domain_key, pattern in rob2_patterns:
        if re.search(pattern, header_lower):
            return domain_key
    
    # Fallback to generic domain patterns
    for domain_key, domain_pattern in ROB_DOMAINS.items():
        if re.search(domain_pattern, header_lower):
            return domain_key
    
    return None


def normalize_rob_cell_value(cell_value: str) -> str | None:
    """
    Normalize ROB cell values to standard terms.
    E.g., "High risk" → "high", "Some concerns" → "unclear"
    """
    if not cell_value:
        return None
    
    normalized = normalize(cell_value).lower()
    
    # Direct matches
    for rob_val in ROB_VALUES:
        if normalized == rob_val:
            return rob_val
    
    # Handle phrases like "High risk", "Low risk", etc.
    if "high" in normalized:
        return "high"
    if "low" in normalized:
        return "low"
    if "unclear" in normalized or "some concern" in normalized or "concern" in normalized:
        return "unclear"
    if "critical" in normalized:
        return "critical"
    
    # Numeric values
    if normalized.isdigit():
        return normalized
    
    # Yes/No values
    if normalized in ["yes", "no", "partial", "n/a", "na"]:
        return normalized
    
    return None


def normalize_rob_table(table: dict[str, Any], section: str | None = None) -> list[dict[str, Any]]:
    """
    Extract structured bias domain records from a ROB table.
    
    Handles RoB 2 table structure:
    - Column 0: Study names (study_name / row_label)
    - Columns 1+: Each column is one bias domain; header describes the domain; 
                  cells contain risk level
    
    Returns:
        List of {bias_domain, bias_value, study_name, column_header, row_index, confidence} records.
    """
    if not table or not table.get("rows"):
        return []
    
    header = table.get("header", [])
    rows = table.get("rows", [])
    records = []
    
    if len(header) < 2:  # Need at least study column + 1 domain column
        return []
    
    # Normalize headers
    norm_header = [normalize(h).lower() for h in header]
    
    # Column 0 is study names
    study_col_idx = 0
    
    # Columns 1+ are potential domain columns (each header might be a domain)
    domain_col_indices = list(range(1, len(header)))
    
    # Extract domain from each column header
    domain_mappings = {}  # col_idx -> (domain_key, confidence)
    for col_idx in domain_col_indices:
        domain = extract_bias_domain_from_header(norm_header[col_idx])
        if domain:
            domain_mappings[col_idx] = (domain, 0.9)  # High confidence if we extracted domain
    
    # If we found domains in headers, use those columns
    if domain_mappings:
        value_col_indices = list(domain_mappings.keys())
    else:
        # Fallback: assume all non-study columns have values
        value_col_indices = domain_col_indices
        # Try to infer domains from first few rows' data patterns
        for col_idx in value_col_indices:
            domain_mappings[col_idx] = (None, 0.5)  # Low confidence fallback
    
    # Parse rows
    for row_idx, row in enumerate(rows):
        # Get study/row name from column 0
        study_name = None
        if study_col_idx < len(row):
            study_name = normalize(row[study_col_idx])
        
        if not study_name or study_name.lower() in ["", "study", "overall"]:
            continue  # Skip rows without a study name
        
        # Extract risk values from domain columns
        for col_idx in value_col_indices:
            if col_idx >= len(row):
                continue
            
            cell_value = normalize(row[col_idx])
            if not cell_value:
                continue
            
            # Normalize the cell value
            normalized_value = normalize_rob_cell_value(cell_value)
            if not normalized_value:
                continue
            
            # Get bias domain for this column
            bias_domain = None
            domain_confidence = 0.5
            
            if col_idx in domain_mappings:
                bias_domain, domain_confidence = domain_mappings[col_idx]
            
            # If domain not extracted from header, try to infer from study name
            if not bias_domain and study_name:
                bias_domain = extract_bias_domain_from_header(study_name)
            
            # Only create record if we have a domain
            if bias_domain:
                col_header = header[col_idx] if col_idx < len(header) else ""
                records.append({
                    "bias_domain": bias_domain,
                    "bias_value": normalized_value,
                    "study_name": study_name,  # Fixed: was "domain_name"
                    "column_header": col_header,
                    "row_index": row_idx,
                    "confidence": min(domain_confidence, 0.95),
                })
    
    return records


def extract_rob_from_sections_images(sections: list[dict[str, Any]], paper_id: str | None = None) -> list[dict[str, Any]]:
    """
    Extract ROB artifacts from images within document sections.
    
    Args:
        sections: List of {heading, images, ...} dicts
        paper_id: Paper identifier
    
    Returns:
        List of OCR ROB artifacts.
    """
    artifacts = []
    
    for section in sections:
        section_heading = section.get("heading")
        local_images = section.get("images", [])
        
        if local_images:
            ocr_artifacts = extract_rob_from_images(local_images, section=section_heading, paper_id=paper_id)
            artifacts.extend(ocr_artifacts)
    
    return artifacts


