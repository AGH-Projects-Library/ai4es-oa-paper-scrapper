export interface PaperSection {
  id: string;
  name: string;
}

export interface ResolvedPaper {
  doi: string;
  title: string;
  source: string;
  authors: string[];
  emails: string[];
  availableSections: PaperSection[];
}