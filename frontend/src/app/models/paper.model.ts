export interface PaperSection {
  id: string;
  name: string;
}

export interface ResolvedPaper {
  doi: string;
  title: string;
  availableSections: PaperSection[];
}