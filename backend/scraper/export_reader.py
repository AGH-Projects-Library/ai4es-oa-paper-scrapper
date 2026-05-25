# Source: notebooks/scraper/export_reader.py
"""
Export Reader Library

Provides utilities to load and parse the simplified JSON export format into
pandas DataFrames and extract document data (tables, images, metadata).

Usage:
    from scraper.export_reader import ExportReader

    reader = ExportReader('path/to/processed_export_*.json')
    df = reader.get_documents_dataframe()

    # Get all tables
    tables_df = reader.get_all_tables_dataframe()

    # Get specific document
    doc = reader.get_document('PMC6706894')
    tables = reader.get_document_tables(doc)
    images = reader.get_document_images(doc)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd

class ExportReader:
    """Load and parse simplified JSON export format."""

    def __init__(self, json_path: str):
        """
        Initialize reader with path to JSON export.

        Args:
            json_path: Path to processed_export_*.json file

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If JSON is invalid
        """
        self.json_path = Path(json_path).resolve()
        if not self.json_path.exists():
            raise FileNotFoundError(f"Export file not found: {self.json_path}")

        # Determine base_dir (parent's parent of JSON file)
        # JSON is in: data/exports/processed_export_*.json
        # base_dir should be: data/
        self.base_dir = self.json_path.parent.parent.resolve()

        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        if not isinstance(self.data, list):
            raise ValueError("Export JSON must be a list of documents")

    def _resolve_path(self, rel_path: str) -> Path:
        """
        Construct absolute path from relative path in JSON.

        Args:
            rel_path: Relative path as stored in JSON

        Returns:
            Absolute Path object
        """
        return (self.base_dir / rel_path).resolve()

    def get_documents_dataframe(self) -> pd.DataFrame:
        rows = []

        for doc in self.data:
            num_tables = sum(len(sec.get('tables', [])) for sec in doc.get('sections', []))
            num_images = sum(len(sec.get('images', [])) for sec in doc.get('sections', []))

            row = {
                'paper_id': doc.get('paper_id'),
                'source': doc.get('source'),
                'pmcid': doc.get('pmcid'),
                'arxiv_id': doc.get('arxiv_id'),
                'authors': doc.get('authors', []),
                'emails': doc.get('emails', []),
                'md_path': doc.get('md_path'),
                'html_path': doc.get('html_path'),
                'pdf_path': doc.get('pdf_path'),
                'extraction_method': doc.get('extraction_method'),
                'num_sections': len(doc.get('sections', [])),
                'num_tables': num_tables,
                'num_images': num_images,
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def get_all_tables_dataframe(self) -> pd.DataFrame:
        rows = []

        for doc in self.data:
            paper_id = doc.get('paper_id')

            for sec in doc.get('sections', []):
                section_heading = sec.get('heading')

                for table in sec.get('tables', []):
                    row = {
                        'paper_id': paper_id,
                        'section': section_heading,
                        'table_index': table.get('table_index'),
                        'global_index': table.get('global_index'),
                        'csv_path': table.get('csv_path'),
                    }
                    rows.append(row)

        return pd.DataFrame(rows)

    def get_all_images_dataframe(self) -> pd.DataFrame:
        rows = []

        for doc in self.data:
            paper_id = doc.get('paper_id')

            for sec in doc.get('sections', []):
                section_heading = sec.get('heading')

                for img in sec.get('images', []):
                    row = {
                        'paper_id': paper_id,
                        'section': section_heading,
                        'placeholder': img.get('placeholder'),
                        'caption': img.get('caption'),
                        'path': img.get('path'),
                    }
                    rows.append(row)

        return pd.DataFrame(rows)

    def get_document(self, paper_id: str) -> Optional[Dict[str, Any]]:
        for doc in self.data:
            if doc.get('paper_id') == paper_id:
                return doc
        return None

    def get_document_tables(self, document: Optional[Dict] = None,
                          paper_id: Optional[str] = None) -> List[Dict]:
        if document is None:
            if paper_id is None:
                raise ValueError("Must provide either document or paper_id")
            document = self.get_document(paper_id)

        if document is None:
            return []

        tables = []
        for sec in document.get('sections', []):
            for table in sec.get('tables', []):
                table_with_section = {**table, 'section': sec.get('heading')}
                tables.append(table_with_section)

        return tables

    def get_document_images(self, document: Optional[Dict] = None,
                           paper_id: Optional[str] = None) -> List[Dict]:
        if document is None:
            if paper_id is None:
                raise ValueError("Must provide either document or paper_id")
            document = self.get_document(paper_id)

        if document is None:
            return []

        images = []
        for sec in document.get('sections', []):
            for img in sec.get('images', []):
                img_with_section = {**img, 'section': sec.get('heading')}
                images.append(img_with_section)

        return images

    def get_section_tables(self, paper_id: str, section_index: int) -> List[Dict]:
        doc = self.get_document(paper_id)
        if not doc or section_index >= len(doc.get('sections', [])):
            return []

        section = doc['sections'][section_index]
        tables = []
        for table in section.get('tables', []):
            table_with_section = {**table, 'section': section.get('heading')}
            tables.append(table_with_section)

        return tables

    def get_section_images(self, paper_id: str, section_index: int) -> List[Dict]:
        doc = self.get_document(paper_id)
        if not doc or section_index >= len(doc.get('sections', [])):
            return []

        section = doc['sections'][section_index]
        images = []
        for img in section.get('images', []):
            img_with_section = {**img, 'section': section.get('heading')}
            images.append(img_with_section)

        return images

    def get_document_metadata(self, paper_id: str) -> Optional[Dict[str, Any]]:
        doc = self.get_document(paper_id)
        if doc is None:
            return None

        return {
            'paper_id': doc.get('paper_id'),
            'source': doc.get('source'),
            'pmcid': doc.get('pmcid'),
            'arxiv_id': doc.get('arxiv_id'),
            'authors': doc.get('authors', []),
            'emails': doc.get('emails', []),
            'md_path': doc.get('md_path'),
            'html_path': doc.get('html_path'),
            'pdf_path': doc.get('pdf_path'),
            'extraction_method': doc.get('extraction_method'),
            'num_sections': len(doc.get('sections', [])),
            'num_tables': sum(len(sec.get('tables', [])) for sec in doc.get('sections', [])),
            'num_images': sum(len(sec.get('images', [])) for sec in doc.get('sections', [])),
        }

    def load_table_csv(self, csv_path: str) -> pd.DataFrame:
        abs_path = self._resolve_path(csv_path)

        if not abs_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path} (resolved to: {abs_path})")

        return pd.read_csv(abs_path)

    def get_file_path(self, rel_path: str) -> str:
        if rel_path.startswith('http://') or rel_path.startswith('https://'):
            return rel_path

        return str(self._resolve_path(rel_path))

    def load_document_sections(self, paper_id: str) -> List[Dict[str, Any]]:
        doc = self.get_document(paper_id)
        if doc is None:
            return []

        sections = []
        for sec in doc.get('sections', []):
            section_data = {
                'heading': sec.get('heading'),
                'tables': [],
                'images': sec.get('images', []),
            }

            for table in sec.get('tables', []):
                try:
                    csv_df = self.load_table_csv(table['csv_path'])
                    section_data['tables'].append({
                        **table,
                        'data': csv_df
                    })
                except FileNotFoundError:
                    section_data['tables'].append({
                        **table,
                        'data': None,
                        'error': 'CSV file not found'
                    })

            sections.append(section_data)

        return sections

    def get_authors_summary(self) -> pd.DataFrame:
        author_papers = {}

        for doc in self.data:
            paper_id = doc.get('paper_id')
            for author in doc.get('authors', []):
                if author not in author_papers:
                    author_papers[author] = []
                author_papers[author].append(paper_id)

        rows = [
            {
                'author': author,
                'num_papers': len(papers),
                'papers': papers
            }
            for author, papers in sorted(author_papers.items())
        ]

        return pd.DataFrame(rows)

    def search_papers(self, query: str, field: str = 'paper_id') -> pd.DataFrame:
        docs_df = self.get_documents_dataframe()

        if field not in docs_df.columns:
            raise ValueError(f"Field '{field}' not found in documents")

        if field in ['authors', 'emails']:
            mask = docs_df[field].apply(
                lambda x: any(query.lower() in str(item).lower() for item in x)
            )
        else:
            mask = docs_df[field].astype(str).str.contains(query, case=False, na=False)

        return docs_df[mask]

    def export_subset(self, paper_ids: List[str], output_path: str) -> None:
        subset = [doc for doc in self.data if doc.get('paper_id') in paper_ids]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subset, f, ensure_ascii=False, indent=2)

        print(f"Exported {len(subset)} documents to {output_path}")

    def get_all_sections_dataframe(self) -> pd.DataFrame:
        rows = []

        for doc in self.data:
            paper_id = doc.get('paper_id')

            for sec_idx, sec in enumerate(doc.get('sections', [])):
                row = {
                    'paper_id': paper_id,
                    'section_index': sec_idx,
                    'heading': sec.get('heading'),
                    'md_path': sec.get('md_path', ''),
                    'num_tables': len(sec.get('tables', [])),
                    'num_images': len(sec.get('images', [])),
                }
                rows.append(row)

        return pd.DataFrame(rows)

    def load_section_markdown(self, md_path: str) -> Optional[str]:
        if not md_path:
            return None

        try:
            abs_path = self._resolve_path(md_path)
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def load_section_with_content(self, paper_id: str, section_index: int) -> Optional[Dict[str, Any]]:
        doc = self.get_document(paper_id)
        if not doc or section_index >= len(doc.get('sections', [])):
            return None

        section = doc['sections'][section_index]
        md_path = section.get('md_path', '')
        md_content = self.load_section_markdown(md_path)

        return {
            'heading': section.get('heading'),
            'md_path': md_path,
            'md_content': md_content,
            'num_tables': len(section.get('tables', [])),
            'num_images': len(section.get('images', []))
        }

    def print_summary(self) -> None:
        print("=" * 60)
        print("EXPORT SUMMARY")
        print("=" * 60)
        print(f"Total documents: {len(self.data)}")
        print(f"Export file: {self.json_path}")

        df_docs = self.get_documents_dataframe()
        df_tables = self.get_all_tables_dataframe()
        df_images = self.get_all_images_dataframe()

        print(f"\nDocuments by source:")
        print(df_docs['source'].value_counts().to_string())

        print(f"\nTotal tables: {len(df_tables)}")
        print(f"Total images: {len(df_images)}")

        print(f"\nDocument sections:")
        print(f"  Min sections: {df_docs['num_sections'].min()}")
        print(f"  Max sections: {df_docs['num_sections'].max()}")
        print(f"  Avg sections: {df_docs['num_sections'].mean():.1f}")

        print("\n" + "=" * 60)


def load_latest_export(exports_dir: Optional[str] = None) -> ExportReader:
    """
    Load the latest processed_export_*.json file from the exports directory.

    Args:
        exports_dir: Path to exports directory. If None, uses data/exports
                    relative to the scraper module location.

    Returns:
        ExportReader instance

    Raises:
        FileNotFoundError: If no export files found
    """
    if exports_dir is None:
        # scraper module is at: backend/scraper/export_reader.py
        # exports should be at: backend/data/exports/
        module_dir = Path(__file__).parent  # backend/scraper/
        exports_dir = str(module_dir.parent / "data" / "exports")

    exports_path = Path(exports_dir).resolve()
    exports = sorted(exports_path.glob("processed_export_*.json"))

    if not exports:
        raise FileNotFoundError(f"No exports found in {exports_path}")

    latest = exports[-1]
    print(f"Loading latest export: {latest.name}")
    return ExportReader(str(latest))
