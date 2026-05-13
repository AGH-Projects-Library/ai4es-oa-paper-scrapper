"""
Cross-paper ROB comparison focused on experiments (study names).

Extracts study names from ROB tables and compares bias assessments of the same
experiment across different papers to identify consistency/conflicts.

Report structure:
- Experiment (study name)
  - Bias domains
    - Papers assessing this domain
    - Consensus value and agreement rate
"""

import json
from typing import Any, Dict, List
from collections import defaultdict


def extract_experiments_from_paper(rob_artifacts: List[Dict[str, Any]], paper_id: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract experiments (study names) and their ROB assessments from a paper's ROB artifacts.
    
    Args:
        rob_artifacts: List of ROB artifacts from the export
        paper_id: Paper identifier
        
    Returns:
        Dict: {
            experiment_name: {
                selection: value,
                performance: value,
                ...
            }
        }
    """
    experiments = {}
    
    # Process table artifacts (have structured normalized records)
    for artifact in rob_artifacts:
        if artifact.get("artifact_type") == "table" and "normalized_records" in artifact:
            for record in artifact["normalized_records"]:
                study_name = record.get("study_name")
                bias_domain = record.get("bias_domain")
                bias_value = record.get("bias_value")
                
                if study_name and bias_domain and bias_value:
                    if study_name not in experiments:
                        experiments[study_name] = {}
                    
                    experiments[study_name][bias_domain] = {
                        "value": bias_value,
                        "confidence": record.get("confidence", 0.5)
                    }
    
    return experiments


def build_experiment_matrix(papers_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build a matrix of experiments and their ROB assessments across papers.
    
    Returns:
        {
            experiment_name: {
                domains: {
                    domain: {
                        papers: {paper_id: value},
                        consensus: value,
                        agreement: 0.0-1.0,
                        unique_values: [...]
                    }
                },
                paper_count: int,
                papers: [paper_ids]
            }
        }
    """
    experiment_matrix = defaultdict(lambda: {
        "domains": defaultdict(lambda: {
            "papers": {},
            "values": defaultdict(int)
        }),
        "papers": set()
    })
    
    # Collect all experiments and their assessments
    for paper_data in papers_data:
        paper_id = paper_data.get("paper_id")
        rob_artifacts = paper_data.get("rob_artifacts", [])
        
        if not rob_artifacts:
            continue
        
        experiments = extract_experiments_from_paper(rob_artifacts, paper_id)
        
        for exp_name, domains in experiments.items():
            experiment_matrix[exp_name]["papers"].add(paper_id)
            
            for domain, assessment in domains.items():
                value = assessment["value"]
                experiment_matrix[exp_name]["domains"][domain]["papers"][paper_id] = value
                experiment_matrix[exp_name]["domains"][domain]["values"][value] += 1
    
    # Calculate consensus and agreement for each domain
    result = {}
    for exp_name, exp_data in experiment_matrix.items():
        result[exp_name] = {
            "paper_count": len(exp_data["papers"]),
            "papers": sorted(list(exp_data["papers"])),
            "domains": {}
        }
        
        for domain, domain_data in exp_data["domains"].items():
            papers_assessing = domain_data["papers"]
            value_counts = domain_data["values"]
            
            if not papers_assessing:
                continue
            
            unique_values = list(value_counts.keys())
            consensus_value = max(value_counts.items(), key=lambda x: x[1])[0] if value_counts else None
            agreement = max(value_counts.values()) / len(papers_assessing) if papers_assessing else 0
            
            result[exp_name]["domains"][domain] = {
                "papers": papers_assessing,
                "paper_count": len(papers_assessing),
                "consensus_value": consensus_value,
                "agreement_rate": round(agreement, 2),
                "value_distribution": dict(value_counts),
                "unique_values": unique_values,
                "has_conflict": len(unique_values) > 1
            }
    
    return result


def generate_experiment_report(papers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive ROB report organized by experiments.
    
    Returns:
        {
            "total_papers": int,
            "total_experiments": int,
            "experiments": {
                exp_name: {
                    domains: {...},
                    ...
                }
            },
            "conflicting_experiments": [...],
            "high_agreement_experiments": [...]
        }
    """
    experiment_matrix = build_experiment_matrix(papers_data)
    
    # Identify experiments with conflicts and high agreement
    conflicting = []
    high_agreement = []
    
    for exp_name, exp_data in experiment_matrix.items():
        has_conflict = any(d.get("has_conflict", False) for d in exp_data["domains"].values())
        if has_conflict:
            conflicting.append(exp_name)
        
        # Check if most domains have high agreement (>75%)
        if exp_data["domains"]:
            avg_agreement = sum(d.get("agreement_rate", 0) for d in exp_data["domains"].values()) / len(exp_data["domains"])
            if avg_agreement > 0.75:
                high_agreement.append((exp_name, round(avg_agreement, 2)))
    
    high_agreement.sort(key=lambda x: x[1], reverse=True)
    
    return {
        "total_papers": len(papers_data),
        "papers_with_rob": len([p for p in papers_data if p.get("rob_artifacts")]),
        "total_experiments": len(experiment_matrix),
        "experiments": experiment_matrix,
        "conflicting_experiments": sorted(conflicting),
        "high_agreement_experiments": high_agreement,
        "summary": {
            "total_experiments_assessed": len(experiment_matrix),
            "experiments_with_conflicts": len(conflicting),
            "experiments_with_high_agreement": len(high_agreement)
        }
    }


def print_experiment_report(report: Dict[str, Any], max_experiments: int = None):
    """Pretty-print experiment report."""
    
    print("\n" + "="*80)
    print("ROB ASSESSMENT REPORT BY EXPERIMENTS")
    print("="*80)
    
    summary = report["summary"]
    print(f"\nOverall Statistics:")
    print(f"  Papers analyzed: {report['papers_with_rob']}/{report['total_papers']}")
    print(f"  Unique experiments: {summary['total_experiments_assessed']}")
    print(f"  Experiments with conflicts: {summary['experiments_with_conflicts']}")
    print(f"  Experiments with high agreement: {summary['experiments_with_high_agreement']}\n")
    
    # List high agreement experiments
    if report["high_agreement_experiments"]:
        print("HIGH AGREEMENT EXPERIMENTS (>75% consensus):")
        for exp_name, avg_agr in report["high_agreement_experiments"][:10]:
            print(f"  ✓ {exp_name} ({int(avg_agr*100)}% agreement)")
    
    # List conflicting experiments
    if report["conflicting_experiments"]:
        print("\nCONFLICTING EXPERIMENTS (varying ROB assessments):")
        for exp_name in report["conflicting_experiments"][:10]:
            exp_data = report["experiments"][exp_name]
            print(f"  ✗ {exp_name} ({exp_data['paper_count']} papers)")
    
    # Detailed experiment data (limited)
    experiments = report["experiments"]
    displayed_count = 0
    
    print("\n" + "="*80)
    print("EXPERIMENT DETAILS:")
    print("="*80)
    
    for exp_name in sorted(experiments.keys())[:max_experiments or 10]:
        exp_data = experiments[exp_name]
        print(f"\n[{displayed_count+1}] {exp_name}")
        print(f"    Papers assessing: {exp_data['paper_count']}")
        print(f"    Papers: {', '.join(exp_data['papers'][:5])}" + 
              (f" +{len(exp_data['papers'])-5} more" if len(exp_data['papers']) > 5 else ""))
        
        for domain, domain_data in exp_data["domains"].items():
            agreement_pct = int(domain_data["agreement_rate"] * 100)
            status = "✓" if not domain_data["has_conflict"] else "✗"
            print(f"      {status} {domain}: {domain_data['consensus_value']} ({agreement_pct}% agree)")
            
            if domain_data["has_conflict"]:
                print(f"         Values: {domain_data['value_distribution']}")
        
        displayed_count += 1


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rob_comparison_by_experiments.py <export_json_file>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    
    # Load export
    with open(export_file, "r") as f:
        papers_data = json.load(f)
    
    # Generate report
    report = generate_experiment_report(papers_data)
    
    # Print report
    print_experiment_report(report, max_experiments=20)
    
    # Save report JSON
    output_file = export_file.replace(".json", "_experiment_report.json")
    with open(output_file, "w") as f:
        # Convert sets to lists for JSON serialization
        report_serializable = json.loads(json.dumps(report, default=str))
        json.dump(report_serializable, f, indent=2)
    
    print(f"\n[SAVED] Full report to {output_file}")
