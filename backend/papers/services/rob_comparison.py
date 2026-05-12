"""
Cross-paper ROB (Risk of Bias) comparison and alignment module.

Enables comparison of ROB assessments across multiple papers:
- Aligns ROB tables by bias domain
- Identifies matching/conflicting bias values
- Generates summary reports
"""

from typing import Any, Dict, List, Tuple
from collections import defaultdict
import json


def align_rob_tables_by_domain(papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Align ROB tables from multiple papers by bias domain.
    
    Args:
        papers_data: List of paper dicts with 'paper_id', 'source', 'rob_artifacts' keys
    
    Returns:
        {
            'domain_matrix': { domain: { paper_id: bias_value } },
            'conflicts': [{ domain, paper_ids_with_conflicts, values }],
            'coverage': { domain: num_papers_with_data },
            'summary': { domain: consensus_value },
        }
    """
    domain_matrix = defaultdict(dict)
    conflicts = []
    coverage = defaultdict(int)
    
    # Extract normalized ROB records from each paper
    for paper_data in papers_data:
        paper_id = paper_data.get('paper_id', 'unknown')
        rob_artifacts = paper_data.get('rob_artifacts', [])
        
        # Find table artifacts with normalized records
        for artifact in rob_artifacts:
            if artifact.get('artifact_type') == 'table' and 'normalized_records' in artifact:
                normalized_records = artifact['normalized_records']
                
                for record in normalized_records:
                    bias_domain = record.get('bias_domain')
                    bias_value = record.get('bias_value')
                    
                    if bias_domain and bias_value:
                        if paper_id not in domain_matrix[bias_domain]:
                            domain_matrix[bias_domain][paper_id] = bias_value
                            coverage[bias_domain] += 1
    
    # Detect conflicts (same domain, different values across papers)
    for domain, paper_values in domain_matrix.items():
        unique_values = set(paper_values.values())
        if len(unique_values) > 1:
            conflicts.append({
                'bias_domain': domain,
                'paper_ids_with_conflicts': list(paper_values.keys()),
                'values_by_paper': paper_values,
                'unique_values': list(unique_values),
                'confidence': 0.75,
            })
    
    # Generate consensus/summary for each domain
    summary = {}
    for domain, paper_values in domain_matrix.items():
        # Simple majority voting for consensus
        value_counts = defaultdict(int)
        for value in paper_values.values():
            value_counts[value] += 1
        
        if value_counts:
            consensus = max(value_counts.items(), key=lambda x: x[1])[0]
            agreement = max(value_counts.values()) / len(paper_values)
            summary[domain] = {
                'consensus_value': consensus,
                'agreement_rate': round(agreement, 2),
                'value_distribution': dict(value_counts),
            }
    
    return {
        'domain_matrix': dict(domain_matrix),
        'conflicts': conflicts,
        'coverage': dict(coverage),
        'summary': summary,
    }


def extract_section_level_rob(papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract section-level ROB artifacts (text mentions) across papers.
    
    Returns:
        {
            'by_section': { section_name: [{ paper_id, match, confidence }] },
            'popular_sections': [(section_name, count)],
            'paper_section_coverage': { paper_id: [section_names] },
        }
    """
    section_artifacts = defaultdict(list)
    paper_sections = defaultdict(set)
    
    for paper_data in papers_data:
        paper_id = paper_data.get('paper_id', 'unknown')
        rob_artifacts = paper_data.get('rob_artifacts', [])
        
        # Find section artifacts (text mentions)
        for artifact in rob_artifacts:
            if artifact.get('artifact_type') == 'section':
                section_name = artifact.get('section', 'unknown')
                match = artifact.get('match', '')
                confidence = artifact.get('confidence', 0.0)
                
                section_artifacts[section_name].append({
                    'paper_id': paper_id,
                    'match': match[:100],  # Truncate
                    'confidence': confidence,
                })
                
                paper_sections[paper_id].add(section_name)
    
    # Count popular sections
    popular_sections = sorted(
        [(section, len(artifacts)) for section, artifacts in section_artifacts.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        'by_section': dict(section_artifacts),
        'popular_sections': popular_sections,
        'paper_section_coverage': {pid: list(sections) for pid, sections in paper_sections.items()},
    }


def extract_ocr_artifacts(papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract OCR-based ROB artifacts (from images) across papers.
    
    Returns:
        {
            'by_paper': { paper_id: [{ section, method, confidence, text_preview }] },
            'total_ocr_artifacts': count,
            'average_confidence': float,
            'methods_used': { method_name: count },
        }
    """
    ocr_by_paper = defaultdict(list)
    method_counts = defaultdict(int)
    confidences = []
    
    for paper_data in papers_data:
        paper_id = paper_data.get('paper_id', 'unknown')
        rob_artifacts = paper_data.get('rob_artifacts', [])
        
        # Find OCR artifacts
        for artifact in rob_artifacts:
            if artifact.get('artifact_type') == 'ocr_table':
                method = artifact.get('method', 'ocr_table')
                confidence = artifact.get('confidence', 0.0)
                
                ocr_by_paper[paper_id].append({
                    'section': artifact.get('section', 'unknown'),
                    'method': method,
                    'confidence': confidence,
                    'text_preview': artifact.get('text', '')[:80],
                    'image_path': artifact.get('image_path', ''),
                })
                
                method_counts[method] += 1
                confidences.append(confidence)
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        'by_paper': dict(ocr_by_paper),
        'total_ocr_artifacts': len(confidences),
        'average_confidence': round(avg_confidence, 3),
        'methods_used': dict(method_counts),
    }


def generate_comparison_report(papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive cross-paper ROB comparison report.
    
    Returns:
        {
            'summary': { num_papers, total_artifacts, ... },
            'table_alignment': { ... from align_rob_tables_by_domain },
            'section_artifacts': { ... from extract_section_level_rob },
            'ocr_artifacts': { ... from extract_ocr_artifacts },
            'recommendations': [...],
        }
    """
    table_alignment = align_rob_tables_by_domain(papers_data)
    section_artifacts = extract_section_level_rob(papers_data)
    ocr_artifacts = extract_ocr_artifacts(papers_data)
    
    # Count total artifacts
    total_text_artifacts = sum(len(v) for v in section_artifacts['by_section'].values())
    total_table_artifacts = sum(
        len(records) for paper in papers_data 
        for artifact in paper.get('rob_artifacts', [])
        if artifact.get('artifact_type') == 'table' and 'normalized_records' in artifact
        for records in [artifact.get('normalized_records', [])]
    )
    total_ocr_artifacts = ocr_artifacts['total_ocr_artifacts']
    
    # Generate recommendations
    recommendations = []
    
    # Recommend investigation of conflicts
    if table_alignment['conflicts']:
        recommendations.append({
            'type': 'investigate_conflicts',
            'message': f"Found {len(table_alignment['conflicts'])} bias domains with conflicting assessments. Review papers for methodological differences.",
            'conflicts': len(table_alignment['conflicts']),
        })
    
    # Recommend high-confidence OCR results
    if ocr_artifacts['average_confidence'] >= 0.8:
        recommendations.append({
            'type': 'high_confidence_ocr',
            'message': f"OCR extraction achieved average confidence of {ocr_artifacts['average_confidence']:.1%}. Results are reliable for automation.",
            'confidence': ocr_artifacts['average_confidence'],
        })
    
    # Recommend manual review of low-confidence OCR
    if ocr_artifacts['average_confidence'] < 0.7:
        recommendations.append({
            'type': 'review_low_confidence',
            'message': f"OCR extraction has low average confidence ({ocr_artifacts['average_confidence']:.1%}). Manual review recommended.",
            'confidence': ocr_artifacts['average_confidence'],
        })
    
    # Recommend coverage improvement
    total_possible_domains = len(table_alignment['coverage'])
    if total_possible_domains > 0:
        avg_coverage = sum(table_alignment['coverage'].values()) / len(table_alignment['coverage'])
        if avg_coverage < len(papers_data) * 0.7:
            recommendations.append({
                'type': 'improve_coverage',
                'message': f"ROB domains have incomplete coverage ({avg_coverage:.1f}/{len(papers_data)} papers on average). Some papers may lack explicit ROB assessments.",
                'avg_coverage': round(avg_coverage, 1),
            })
    
    return {
        'summary': {
            'num_papers': len(papers_data),
            'total_text_artifacts': total_text_artifacts,
            'total_table_artifacts': total_table_artifacts,
            'total_ocr_artifacts': total_ocr_artifacts,
            'total_artifacts': total_text_artifacts + total_table_artifacts + total_ocr_artifacts,
        },
        'table_alignment': table_alignment,
        'section_artifacts': section_artifacts,
        'ocr_artifacts': ocr_artifacts,
        'recommendations': recommendations,
    }


def export_comparison_report(papers_data: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate and export a comprehensive ROB comparison report to JSON.
    
    Returns:
        Path to the exported JSON file.
    """
    report = generate_comparison_report(papers_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return output_path


if __name__ == '__main__':
    """
    Quick test of ROB comparison functionality.
    
    For full examples, see:
    - rob_comparison_example.py: Example with sample hardcoded data
    - rob_comparison_from_export.py: Real data from to_json.py export
    """
    print("Testing ROB comparison module...")
    
    # Simple test data
    test_papers = [
        {
            'paper_id': 'TEST001',
            'rob_artifacts': [
                {
                    'artifact_type': 'table',
                    'normalized_records': [
                        {'bias_domain': 'selection', 'bias_value': 'low'},
                    ]
                }
            ]
        }
    ]
    
    try:
        report = generate_comparison_report(test_papers)
        print("✅ ROB comparison module is working!")
        print(f"   Found {report['summary']['total_artifacts']} artifacts")
        print("\nFor full examples, run:")
        print("  python rob_comparison_example.py")
        print("  python rob_comparison_from_export.py <export.json>")
    except Exception as e:
        print(f"❌ Error: {e}")
