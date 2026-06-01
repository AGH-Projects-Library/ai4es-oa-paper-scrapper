import { Component, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { of, forkJoin } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatStepper, MatStepperModule } from '@angular/material/stepper';
import { MatTabsModule } from '@angular/material/tabs';

import { Doi } from '../../services/doi';
import { ApiRequestError } from '../../models/api-error.model';
import {
  BatchPaperFull,
  BatchResult,
  PaperSection,
  ResolvedPaper,
} from '../../models/paper.model';
import { RobArtifacts } from '../paper-sections-stepper/rob-artifacts/rob-artifacts';
import { TablesViewer } from '../paper-sections-stepper/tables-viewer/tables-viewer';
import { ImagesViewer } from '../paper-sections-stepper/images-viewer/images-viewer';

type Step1State = 'idle' | 'loading' | 'done' | 'error';
type ResolveState = 'idle' | 'done';
type ContentState = 'idle' | 'loading' | 'done' | 'error';
type InputMode = 'text' | 'file';

interface SemanticCategory {
  id: string;
  label: string;
  keyword: string;
  icon: string;
  description: string;
}

const SEMANTIC_CATEGORIES: SemanticCategory[] = [
  { id: 'intro',      label: 'Introduction',  keyword: 'introduction', icon: 'article',     description: 'Background and research context' },
  { id: 'methods',    label: 'Methods',       keyword: 'method',       icon: 'science',     description: 'Study design and procedures' },
  { id: 'results',    label: 'Results',       keyword: 'result',       icon: 'bar_chart',   description: 'Findings and outcomes' },
  { id: 'discussion', label: 'Discussion',    keyword: 'discussion',   icon: 'forum',       description: 'Interpretation and implications' },
  { id: 'rob',        label: 'Risk of Bias',  keyword: 'risk of bias', icon: 'fact_check',  description: 'Bias assessment and quality' },
];

@Component({
  selector: 'app-batch-processor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatExpansionModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatStepperModule,
    MatTabsModule,
    RobArtifacts,
    TablesViewer,
    ImagesViewer,
  ],
  templateUrl: './batch-processor.html',
  styleUrl: './batch-processor.scss',
})
export class BatchProcessor {
  @ViewChild('stepper') private stepperEl!: MatStepper;

  private readonly doi = inject(Doi);

  readonly semanticCategories = SEMANTIC_CATEGORIES;

  // Step 1
  readonly inputMode = signal<InputMode>('text');
  readonly doiText = signal('');
  readonly selectedFile = signal<File | null>(null);
  readonly step1State = signal<Step1State>('idle');
  readonly batchResults = signal<BatchResult[]>([]);
  readonly batchSummary = signal<{ total: number; success: number; not_found: number; error: number } | null>(null);
  readonly step1Error = signal('');

  // Between step 1 → 2
  readonly resolveState = signal<ResolveState>('idle');
  readonly resolvedPapers = signal<Map<string, ResolvedPaper>>(new Map());

  // Step 2 — multi-select categories
  readonly selectedCategories = signal<Set<string>>(new Set(['intro']));
  readonly showCustom = signal<boolean>(false);
  readonly customKeyword = signal<string>('');

  // Step 3
  readonly contentState = signal<ContentState>('idle');
  readonly paperResults = signal<BatchPaperFull[]>([]);
  readonly contentError = signal('');
  readonly visitedTabs = signal<Map<number, Set<number>>>(new Map());

  // ── Step 2: keywords & matching ───────────────────────────────────────────

  get activeKeywords(): string[] {
    const keywords: string[] = [];
    for (const id of this.selectedCategories()) {
      const cat = SEMANTIC_CATEGORIES.find(c => c.id === id);
      if (cat) keywords.push(cat.keyword);
    }
    const custom = this.customKeyword().trim();
    if (custom) keywords.push(custom);
    return keywords;
  }

  toggleCategory(id: string): void {
    const current = new Set(this.selectedCategories());
    if (current.has(id)) {
      current.delete(id);
    } else {
      current.add(id);
    }
    this.selectedCategories.set(current);
  }

  toggleCustom(): void {
    const next = !this.showCustom();
    this.showCustom.set(next);
    if (!next) this.customKeyword.set('');
  }

  // Returns subsections of the section at parentIdx — sections whose name starts
  // with "N.N" following a parent section (either unnumbered or "N Title").
  private getSubsectionIdsInPaper(sections: PaperSection[], parentIdx: number): string[] {
    const parent = sections[parentIdx];
    if (/^\d+\.\d+/.test(parent.name)) return [];   // parent is itself a subsection

    const parentNumMatch = parent.name.match(/^(\d+)\s/);
    const result: string[] = [];

    for (let i = parentIdx + 1; i < sections.length; i++) {
      const s = sections[i];
      const childNumMatch = s.name.match(/^(\d+)\.\d+/);
      if (!childNumMatch) break;                     // non-numbered → end of block

      if (parentNumMatch) {
        if (childNumMatch[1] === parentNumMatch[1]) result.push(s.id);
        else break;
      } else {
        result.push(s.id);
      }
    }
    return result;
  }

  private matchesByKeyword(sectionName: string, keywords: string[]): boolean {
    if (!keywords.length) return false;
    const lower = sectionName.toLowerCase();
    return keywords.some(kw => lower.includes(kw.toLowerCase()));
  }

  // Sections matching any keyword + their subsections.
  getMatchingIds(paper: ResolvedPaper): string[] {
    const kws = this.activeKeywords;
    const sections = paper.availableSections;
    const matched = new Set<string>();

    sections.forEach((s, idx) => {
      if (this.matchesByKeyword(s.name, kws)) {
        matched.add(s.id);
        for (const subId of this.getSubsectionIdsInPaper(sections, idx)) {
          matched.add(subId);
        }
      }
    });
    return Array.from(matched);
  }

  // Per-category stats: how many papers and sections match a single keyword (incl. subsections).
  getCategoryStats(keyword: string): { papers: number; sections: number } {
    const resolved = this.resolvedPapers();
    if (!resolved.size) return { papers: 0, sections: 0 };

    let papers = 0;
    let sections = 0;

    resolved.forEach(paper => {
      const secs = paper.availableSections;
      const matched = new Set<string>();
      secs.forEach((s, idx) => {
        if (s.name.toLowerCase().includes(keyword.toLowerCase())) {
          matched.add(s.id);
          for (const subId of this.getSubsectionIdsInPaper(secs, idx)) {
            matched.add(subId);
          }
        }
      });
      if (matched.size > 0) {
        papers++;
        sections += matched.size;
      }
    });
    return { papers, sections };
  }

  canLoadSections(): boolean {
    if (!this.activeKeywords.length || !this.resolvedPapers().size) return false;
    for (const paper of this.resolvedPapers().values()) {
      if (this.getMatchingIds(paper).length > 0) return true;
    }
    return false;
  }

  // ── Per-paper lazy tab tracking ───────────────────────────────────────────

  hasVisitedTab(paperId: number, index: number): boolean {
    return this.visitedTabs().get(paperId)?.has(index) ?? false;
  }

  onPaperTabChange(paperId: number, index: number): void {
    const map = new Map(this.visitedTabs());
    const set = new Set(map.get(paperId) ?? [0]);
    set.add(index);
    map.set(paperId, set);
    this.visitedTabs.set(map);
  }

  // ── Input mode ────────────────────────────────────────────────────────────

  setInputMode(mode: InputMode): void {
    this.inputMode.set(mode);
    this.doiText.set('');
    this.selectedFile.set(null);
  }

  onDoiTextChange(value: string): void {
    this.doiText.set(value);
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile.set(input.files?.[0] ?? null);
  }

  canSubmit(): boolean {
    if (this.step1State() === 'loading') return false;
    if (this.inputMode() === 'text') return this.doiText().trim().length > 0;
    return this.selectedFile() !== null;
  }

  // ── Step 1: batch process ─────────────────────────────────────────────────

  submit(): void {
    this.step1State.set('loading');
    this.batchResults.set([]);
    this.batchSummary.set(null);
    this.step1Error.set('');
    this.resolveState.set('idle');
    this.resolvedPapers.set(new Map());

    const obs = this.inputMode() === 'text'
      ? this.doi.batchProcess(
          this.doiText().split('\n')
            .map(l => l.trim())
            .filter(l => l && !l.startsWith('#')),
        )
      : this.doi.batchProcessUpload(this.selectedFile()!);

    obs.subscribe({
      next: res => {
        this.batchResults.set(res.results);
        this.batchSummary.set(res.summary);
        this.step1State.set('done');

        // Extract ResolvedPaper directly from batch results — no extra API round-trip needed
        const map = new Map<string, ResolvedPaper>();
        res.results
          .filter(r => r.status === 'success' && r.paper)
          .forEach(r => map.set(r.doi, r.paper!));

        if (map.size > 0) {
          this.resolvedPapers.set(map);
          this.resolveState.set('done');
          this.stepperEl.next();
        }
      },
      error: (err: unknown) => {
        this.step1Error.set(
          err instanceof ApiRequestError ? err.message : 'Batch processing failed.',
        );
        this.step1State.set('error');
      },
    });
  }

  // ── Step 3: fetch section content ────────────────────────────────────────

  loadSectionContent(): void {
    if (!this.canLoadSections()) return;

    this.contentState.set('loading');
    this.contentError.set('');
    this.paperResults.set([]);
    this.visitedTabs.set(new Map());

    const resolved = this.resolvedPapers();
    const entries = Array.from(resolved.values());

    const calls = entries.map(paper => {
      const allMatchedIds = this.getMatchingIds(paper);
      const matchedSections: PaperSection[] = paper.availableSections.filter(s =>
        allMatchedIds.includes(s.id),
      );

      if (allMatchedIds.length === 0) {
        return of<BatchPaperFull>({ paper, matchedSections: [], sectionContent: [] });
      }

      return this.doi.fetchSections({ doi: paper.doi, sections: allMatchedIds }).pipe(
        map(res => ({
          paper,
          matchedSections,
          sectionContent: res.sections,
        } satisfies BatchPaperFull)),
        catchError(() => of<BatchPaperFull>({ paper, matchedSections, sectionContent: [] })),
      );
    });

    forkJoin(calls).subscribe({
      next: results => {
        const initMap = new Map<number, Set<number>>();
        results.forEach(r => initMap.set(r.paper.id, new Set([0])));
        this.visitedTabs.set(initMap);
        this.paperResults.set(results);
        this.contentState.set('done');
        this.stepperEl.next();
      },
      error: (err: unknown) => {
        this.contentError.set(
          err instanceof ApiRequestError ? err.message : 'Failed to load section content.',
        );
        this.contentState.set('error');
      },
    });
  }

  // ── Export ────────────────────────────────────────────────────────────────

  private triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  downloadBatchExport(): void {
    const ids = this.paperResults().map(r => r.paper.id);
    if (!ids.length) return;
    const kws = this.activeKeywords;
    this.doi.batchExport(ids, kws.length > 0 ? kws : undefined).subscribe(blob =>
      this.triggerDownload(blob, 'batch_export.zip'),
    );
  }

  downloadCsv(paperId: number): void {
    this.doi.exportCsv(paperId).subscribe(blob =>
      this.triggerDownload(blob, `paper_${paperId}_tables.zip`),
    );
  }

  downloadMarkdown(paperId: number): void {
    this.doi.exportMarkdown(paperId).subscribe(blob =>
      this.triggerDownload(blob, `paper_${paperId}_markdown.zip`),
    );
  }

  downloadJson(paperId: number): void {
    this.doi.exportJson(paperId).subscribe(blob =>
      this.triggerDownload(blob, `paper_${paperId}.json`),
    );
  }

  // ── Reset ─────────────────────────────────────────────────────────────────

  resetFlow(): void {
    this.inputMode.set('text');
    this.doiText.set('');
    this.selectedFile.set(null);
    this.step1State.set('idle');
    this.batchResults.set([]);
    this.batchSummary.set(null);
    this.step1Error.set('');
    this.resolveState.set('idle');
    this.resolvedPapers.set(new Map());
    this.selectedCategories.set(new Set(['intro']));
    this.showCustom.set(false);
    this.customKeyword.set('');
    this.contentState.set('idle');
    this.paperResults.set([]);
    this.contentError.set('');
    this.visitedTabs.set(new Map());
    this.stepperEl.reset();
  }
}
