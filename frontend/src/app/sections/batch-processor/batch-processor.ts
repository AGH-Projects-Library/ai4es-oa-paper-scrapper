import { Component, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
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
import { ResolveDoiSuccessResponse } from '../../models/resolve-doi.model';
import { RobArtifacts } from '../paper-sections-stepper/rob-artifacts/rob-artifacts';
import { TablesViewer } from '../paper-sections-stepper/tables-viewer/tables-viewer';
import { ImagesViewer } from '../paper-sections-stepper/images-viewer/images-viewer';

type Step1State = 'idle' | 'loading' | 'done' | 'error';
type ResolveState = 'idle' | 'loading' | 'done';
type ContentState = 'idle' | 'loading' | 'done' | 'error';
type InputMode = 'text' | 'file';

interface SemanticCategory {
  id: string;
  label: string;
  keyword: string;
}

const SEMANTIC_CATEGORIES: SemanticCategory[] = [
  { id: 'methods',    label: 'Methods',       keyword: 'method' },
  { id: 'results',    label: 'Results',       keyword: 'result' },
  { id: 'discussion', label: 'Discussion',    keyword: 'discussion' },
  { id: 'rob',        label: 'Risk of Bias',  keyword: 'risk of bias' },
  { id: 'intro',      label: 'Introduction',  keyword: 'introduction' },
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
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
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

  // Step 2
  readonly selectedCategory = signal<string>('methods');
  readonly customKeyword = signal<string>('');

  // Step 3
  readonly contentState = signal<ContentState>('idle');
  readonly paperResults = signal<BatchPaperFull[]>([]);
  readonly contentError = signal('');

  // ── Step 2 helpers ────────────────────────────────────────────────────────

  get activeKeyword(): string {
    const cat = SEMANTIC_CATEGORIES.find(c => c.id === this.selectedCategory());
    if (cat) return cat.keyword;
    return this.customKeyword().trim();
  }

  selectCategory(id: string): void {
    this.selectedCategory.set(id);
    this.customKeyword.set('');
  }

  clearCategory(): void {
    this.selectedCategory.set('');
  }

  matchSection(sectionName: string, keyword: string): boolean {
    if (!keyword) return false;
    return sectionName.toLowerCase().includes(keyword.toLowerCase());
  }

  getMatchingIds(paper: ResolvedPaper): string[] {
    const kw = this.activeKeyword;
    return paper.availableSections
      .filter(s => this.matchSection(s.name, kw))
      .map(s => s.id);
  }

  getMatchingPreview(): { papersWithMatch: number; totalSections: number; papersWithout: number } {
    const resolved = this.resolvedPapers();
    let papersWithMatch = 0;
    let totalSections = 0;
    resolved.forEach(paper => {
      const ids = this.getMatchingIds(paper);
      if (ids.length > 0) {
        papersWithMatch++;
        totalSections += ids.length;
      }
    });
    return {
      papersWithMatch,
      totalSections,
      papersWithout: resolved.size - papersWithMatch,
    };
  }

  canLoadSections(): boolean {
    return this.activeKeyword.length > 0 && this.resolvedPapers().size > 0;
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

        const successDois = res.results
          .filter(r => r.status === 'success')
          .map(r => r.doi);

        if (successDois.length > 0) {
          this.loadResolvedPapers(successDois);
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

  // ── Between step 1 → 2: resolve each successful paper ─────────────────────

  private loadResolvedPapers(dois: string[]): void {
    this.resolveState.set('loading');

    const calls = dois.map(doi =>
      this.doi.resolveDoi({ doi }).pipe(
        map(res => (res.status === 'success' ? (res as ResolveDoiSuccessResponse).paper : null)),
        catchError(() => of(null)),
      ),
    );

    forkJoin(calls).subscribe(papers => {
      const map = new Map<string, ResolvedPaper>();
      papers.forEach(p => {
        if (p) map.set(p.doi, p);
      });
      this.resolvedPapers.set(map);
      this.resolveState.set('done');
      this.stepperEl.next();
    });
  }

  // ── Step 3: fetch section content ────────────────────────────────────────

  loadSectionContent(): void {
    if (!this.canLoadSections()) return;

    this.contentState.set('loading');
    this.contentError.set('');
    this.paperResults.set([]);

    const resolved = this.resolvedPapers();
    const entries = Array.from(resolved.values());

    const calls = entries.map(paper => {
      const matchedSections: PaperSection[] = paper.availableSections.filter(s =>
        this.matchSection(s.name, this.activeKeyword),
      );
      const ids = matchedSections.map(s => s.id);

      if (ids.length === 0) {
        return of<BatchPaperFull>({ paper, matchedSections: [], sectionContent: [] });
      }

      return this.doi.fetchSections({ doi: paper.doi, sections: ids }).pipe(
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
    this.doi.batchExport(ids).subscribe(blob =>
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
    this.selectedCategory.set('methods');
    this.customKeyword.set('');
    this.contentState.set('idle');
    this.paperResults.set([]);
    this.contentError.set('');
    this.stepperEl.reset();
  }
}
