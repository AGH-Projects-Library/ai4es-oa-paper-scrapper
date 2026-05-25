"""
Example: ROB Comparison with Sample Data

This script demonstrates the ROB comparison functionality with example data.

Usage:
    python rob_comparison_example.py

Output:
    - Formatted console report
    - rob_comparison_example_report.json (full report with all data)
"""

from rob_comparison import generate_comparison_report, export_comparison_report


def main():
    # Sample paper data with ROB artifacts
    example_papers = [
        {
            'paper_id': 'PMC001',
            'source': 'pmc',
            'title': 'Study on Treatment A vs B',
            'rob_artifacts': [
                {
                    'artifact_type': 'section',
                    'section': 'Assessment of risk of bias',
                    'match': 'risk of bias',
                    'confidence': 0.95,
                    'text': 'We assessed risk of bias using Cochrane tool.',
                },
                {
                    'artifact_type': 'table',
                    'section': 'Risk of bias summary',
                    'normalized_records': [
                        {'bias_domain': 'selection', 'bias_value': 'low', 'domain_name': 'Selection Bias', 'confidence': 0.85},
                        {'bias_domain': 'performance', 'bias_value': 'high', 'domain_name': 'Performance Bias', 'confidence': 0.85},
                        {'bias_domain': 'detection', 'bias_value': 'unclear', 'domain_name': 'Detection Bias', 'confidence': 0.85},
                    ]
                },
            ]
        },
        {
            'paper_id': 'PMC002',
            'source': 'pmc',
            'title': 'Comparative effectiveness study',
            'rob_artifacts': [
                {
                    'artifact_type': 'section',
                    'section': 'Quality assessment',
                    'match': 'Risk of Bias 2',
                    'confidence': 0.92,
                    'text': 'We used the RoB 2 tool for quality assessment.',
                },
                {
                    'artifact_type': 'table',
                    'section': 'Risk of bias in included studies',
                    'normalized_records': [
                        {'bias_domain': 'selection', 'bias_value': 'low', 'domain_name': 'Selection', 'confidence': 0.85},
                        {'bias_domain': 'performance', 'bias_value': 'low', 'domain_name': 'Performance', 'confidence': 0.85},
                        {'bias_domain': 'detection', 'bias_value': 'high', 'domain_name': 'Detection', 'confidence': 0.85},
                        {'bias_domain': 'attrition', 'bias_value': 'low', 'domain_name': 'Attrition', 'confidence': 0.85},
                    ]
                },
            ]
        },
        {
            'paper_id': 'PMC003',
            'source': 'pmc',
            'title': 'Meta-analysis of interventions',
            'rob_artifacts': [
                {
                    'artifact_type': 'section',
                    'section': 'Assessment of risk of bias',
                    'match': 'ROBINS-I',
                    'confidence': 0.90,
                    'text': 'We used ROBINS-I for observational studies.',
                },
                {
                    'artifact_type': 'table',
                    'section': 'Risk of bias assessment',
                    'normalized_records': [
                        {'bias_domain': 'selection', 'bias_value': 'low', 'domain_name': 'Selection', 'confidence': 0.85},
                        {'bias_domain': 'performance', 'bias_value': 'high', 'domain_name': 'Performance', 'confidence': 0.85},
                        {'bias_domain': 'detection', 'bias_value': 'low', 'domain_name': 'Detection', 'confidence': 0.85},
                    ]
                },
            ]
        },
    ]

    print("=" * 80)
    print("ROB COMPARISON REPORT - EXAMPLE WITH SAMPLE DATA")
    print("=" * 80)

    # Generate report
    report = generate_comparison_report(example_papers)

    # Print summary
    print(f"\n📊 SUMMARY")
    print(f"  Papers analyzed: {report['summary']['num_papers']}")
    print(f"  Total artifacts found: {report['summary']['total_artifacts']}")
    print(f"    - Text mentions: {report['summary']['total_text_artifacts']}")
    print(f"    - Table records: {report['summary']['total_table_artifacts']}")
    print(f"    - OCR results: {report['summary']['total_ocr_artifacts']}")

    # Print table alignment
    print(f"\n📋 BIAS DOMAIN ALIGNMENT")
    print(f"  Domains found: {len(report['table_alignment']['domain_matrix'])}")
    for domain, papers_values in report['table_alignment']['domain_matrix'].items():
        print(f"\n  {domain.upper()}")
        for paper_id, value in papers_values.items():
            print(f"    {paper_id}: {value}")

    # Print consensus
    print(f"\n🎯 CONSENSUS (Majority Voting)")
    for domain, summary in report['table_alignment']['summary'].items():
        agreement = summary['agreement_rate']
        consensus = summary['consensus_value']
        print(f"  {domain}: {consensus} ({agreement:.0%} agreement)")

    # Print conflicts
    print(f"\n⚠️  CONFLICTS")
    if report['table_alignment']['conflicts']:
        for conflict in report['table_alignment']['conflicts']:
            domain = conflict['bias_domain']
            values = conflict['unique_values']
            papers = conflict['paper_ids_with_conflicts']
            print(f"  {domain}: {values} (in papers: {papers})")
    else:
        print("  No conflicts detected!")

    # Print popular sections
    print(f"\n📝 POPULAR ROB ASSESSMENT SECTIONS")
    for section, count in report['section_artifacts']['popular_sections'][:5]:
        print(f"  {section}: {count} paper(s)")

    # Print recommendations
    print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])} total)")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec['type']}")
        print(f"     {rec['message']}")

    # Export to JSON
    output_file = 'rob_comparison_example_report.json'
    export_comparison_report(example_papers, output_file)
    print(f"\n✅ Full report exported to: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
