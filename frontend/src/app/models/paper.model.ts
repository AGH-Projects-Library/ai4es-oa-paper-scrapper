export interface PaperSection {
  id: string;
  name: string;
}

export interface SectionResult {
  id: string;
  name: string;
  content: string;
}

export interface RobNormalizedRecord {
  bias_domain: string;
  bias_value: string;
  study_name: string;
  column_header?: string;
  row_index?: number;
  confidence?: number;
}

interface RobArtifactBase {
  artifact_type: 'section' | 'table' | 'ocr_table';
  paper_id: string;
  section: string;
  match?: string;
  confidence: number;
  text: string;
}

export interface RobSectionArtifact extends RobArtifactBase {
  artifact_type: 'section';
}

export interface RobTableArtifact extends RobArtifactBase {
  artifact_type: 'table' | 'ocr_table';
  table?: {
    header: string[];
    rows: string[][];
    markdown: string;
  };
  normalized_records?: RobNormalizedRecord[];
  image_path?: string;
  caption?: string;
  method?: string;
  full_text?: string;
}

export type RobArtifact = RobSectionArtifact | RobTableArtifact;

export interface PaperTableMeta {
  id: number;
  global_index: number;
  section_id: string;
  section_name: string;
  csv_path: string;
}

export interface PaperTableData {
  global_index: number;
  section_id: string;
  section_name: string;
  header: string[];
  rows: string[][];
}

export interface PaperImage {
  id: number;
  idx: number;
  placeholder: string;
  caption: string;
  path: string;
  section_id: string;
  section_name: string;
}

export interface ResolvedPaper {
  id: number;
  doi: string;
  title: string;
  source: string;
  authors: string[];
  emails: string[];
  availableSections: PaperSection[];
  robArtifacts: RobArtifact[];
}

export interface PaperListItem {
  id: number;
  doi: string;
  title: string;
  source: string;
  authors: string[];
  num_sections: number;
  num_tables: number;
  num_images: number;
  processed_at: string;
}

export interface GetPapersResponse {
  status: 'success';
  papers: PaperListItem[];
}

export interface BatchResult {
  doi: string;
  status: 'success' | 'not_found' | 'error';
  paper?: PaperListItem;
  message?: string;
}

export interface BatchProcessResponse {
  status: 'success';
  results: BatchResult[];
  summary: {
    total: number;
    success: number;
    not_found: number;
    error: number;
  };
}
