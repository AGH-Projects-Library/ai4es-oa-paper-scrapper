import { CommonModule } from '@angular/common';
import { Component, ViewChild, effect, signal } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { Doi } from '../../services/doi';
import { PaperSelectionService } from '../../services/paper-selection.service';
import { ApiRequestError } from '../../models/api-error.model';
import { ResolvedPaper, SectionResult } from '../../models/paper.model';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatStepper, MatStepperModule } from '@angular/material/stepper';
import { MatTabsModule } from '@angular/material/tabs';
import { RobArtifacts } from './rob-artifacts/rob-artifacts';
import { TablesViewer } from './tables-viewer/tables-viewer';
import { ImagesViewer } from './images-viewer/images-viewer';

type LookupState = 'idle' | 'loading' | 'success' | 'not_found' | 'service_error';
type ResultState = 'idle' | 'loading' | 'success' | 'error';

@Component({
  selector: 'app-paper-sections-stepper',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatStepperModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatCheckboxModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    RobArtifacts,
    TablesViewer,
    ImagesViewer,
  ],
  templateUrl: './paper-sections-stepper.html',
  styleUrl: './paper-sections-stepper.scss',
})
export class PaperSectionsStepper {
  @ViewChild('stepper') private stepperEl!: MatStepper;

  readonly doiForm: FormGroup<{
    doi: FormControl<string>;
  }>;

  readonly sectionForm: FormGroup<{
    selectedSections: FormControl<string[]>;
  }>;

  readonly lookupState = signal<LookupState>('idle');
  readonly resultState = signal<ResultState>('idle');

  readonly lookupErrorMessage = signal('');
  readonly resultErrorMessage = signal('');

  readonly resolvedPaper = signal<ResolvedPaper | null>(null);
  readonly sectionResults = signal<SectionResult[]>([]);

  readonly tabsVisited = signal<Set<number>>(new Set([0]));

  constructor(
    private fb: FormBuilder,
    private doi: Doi,
    private selectionService: PaperSelectionService,
  ) {
    // When the paper list selects a cached paper, pre-fill the DOI and trigger lookup.
    effect(() => {
      const doi = this.selectionService.pendingDoi();
      if (!doi) return;
      this.doiControl.setValue(doi);
      this.selectionService.clear();
      this.lookupPaper(this.stepperEl);
    });

    // Source: new feature — regex extended to accept arXiv identifiers (e.g. 2410.00123)
    this.doiForm = this.fb.nonNullable.group({
      doi: this.fb.nonNullable.control('', [
        Validators.required,
        Validators.pattern(/^(\d{4}\.\d{4,5}(v\d+)?|10\.\S+\/\S+)$/),
      ]),
    });

    this.sectionForm = this.fb.nonNullable.group({
      selectedSections: this.fb.nonNullable.control<string[]>([], [
        Validators.required,
      ]),
    });
  }

  get doiControl(): FormControl<string> {
    return this.doiForm.controls.doi;
  }

  get selectedSectionsControl(): FormControl<string[]> {
    return this.sectionForm.controls.selectedSections;
  }

  normalizeDoi(value: string): string {
    return value.trim();
  }

  isSectionSelected(sectionId: string): boolean {
    return this.selectedSectionsControl.value.includes(sectionId);
  }

  toggleSection(sectionId: string, checked: boolean): void {
    const current = this.selectedSectionsControl.value;

    if (checked) {
      let updated = current.includes(sectionId) ? current : [...current, sectionId];
      // Auto-select subsections when a parent section is checked
      const paper = this.resolvedPaper();
      if (paper) {
        const subsectionIds = this.getSubsectionIds(paper.availableSections, sectionId);
        for (const subId of subsectionIds) {
          if (!updated.includes(subId)) updated = [...updated, subId];
        }
      }
      this.selectedSectionsControl.setValue(updated);
    } else {
      this.selectedSectionsControl.setValue(current.filter(id => id !== sectionId));
    }

    this.selectedSectionsControl.markAsTouched();
    this.selectedSectionsControl.updateValueAndValidity();
  }

  private getSubsectionIds(sections: { id: string; name: string }[], parentId: string): string[] {
    const parentIdx = sections.findIndex(s => s.id === parentId);
    if (parentIdx === -1) return [];

    const parent = sections[parentIdx];
    // If the parent is itself a numbered subsection (e.g. "2.1 Data"), it has no children
    if (/^\d+\.\d+/.test(parent.name)) return [];

    // Extract leading number from parent name if present (e.g. "2 Methods" → "2")
    const parentNumMatch = parent.name.match(/^(\d+)\s/);
    const result: string[] = [];

    for (let i = parentIdx + 1; i < sections.length; i++) {
      const s = sections[i];
      // A section is a subsection if its name starts with "N.N" or "N.N.N" pattern
      const childNumMatch = s.name.match(/^(\d+)\.\d+/);
      if (!childNumMatch) break;  // Non-numbered section → end of subsection block

      if (parentNumMatch) {
        // Numbered parent: only take children with the same leading number
        if (childNumMatch[1] === parentNumMatch[1]) {
          result.push(s.id);
        } else {
          break;
        }
      } else {
        // Unnumbered parent (e.g. "Methods"): take all following "N.N" sections until next parent
        result.push(s.id);
      }
    }

    return result;
  }

  onTabChange(index: number): void {
    const visited = new Set(this.tabsVisited());
    visited.add(index);
    this.tabsVisited.set(visited);
  }

  lookupPaper(stepper: MatStepper): void {
    this.doiForm.markAllAsTouched();
    if (this.doiForm.invalid) return;

    const normalizedDoi = this.normalizeDoi(this.doiControl.value);
    this.doiControl.setValue(normalizedDoi);

    this.lookupState.set('loading');
    this.lookupErrorMessage.set('');
    this.resultState.set('idle');
    this.resultErrorMessage.set('');
    this.resolvedPaper.set(null);
    this.sectionResults.set([]);
    this.sectionForm.reset({ selectedSections: [] });

    this.doi.resolveDoi({ doi: normalizedDoi }).subscribe({
      next: (response) => {
        if (response.status === 'not_found') {
          this.lookupState.set('not_found');
          this.lookupErrorMessage.set(
            response.message ||
              "We couldn't find a paper for this DOI. Please check the DOI and try again."
          );
          return;
        }

        this.resolvedPaper.set(response.paper);
        this.lookupState.set('success');
        stepper.next();
      },
      error: (err: unknown) => {
        const msg =
          err instanceof ApiRequestError
            ? err.message
            : "We couldn't connect to the lookup service. Please try again.";

        this.lookupState.set('service_error');
        this.lookupErrorMessage.set(msg);
      },
    });
  }

  fetchSelectedSections(stepper: MatStepper): void {
    this.sectionForm.markAllAsTouched();

    const paper = this.resolvedPaper();
    if (this.sectionForm.invalid || !paper) return;

    this.resultState.set('loading');
    this.resultErrorMessage.set('');
    this.sectionResults.set([]);
    this.tabsVisited.set(new Set([0]));
    stepper.next();

    const selectedIds = this.selectedSectionsControl.value;

    this.doi.fetchSections({ doi: paper.doi, sections: selectedIds }).subscribe({
      next: (response) => {
        this.sectionResults.set(response.sections);
        this.resultState.set('success');
      },
      error: (err: unknown) => {
        const msg =
          err instanceof ApiRequestError
            ? err.message
            : "We couldn't load the selected sections. Please try again.";

        this.resultState.set('error');
        this.resultErrorMessage.set(msg);
      },
    });
  }

  // Source: notebooks/scraper/exporters.py — compress_directory() / export_documents()
  private triggerDownload(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  downloadCsv(paperId: number): void {
    this.doi.exportCsv(paperId).subscribe((blob) =>
      this.triggerDownload(blob, `paper_${paperId}_tables.zip`),
    );
  }

  downloadMarkdown(paperId: number): void {
    this.doi.exportMarkdown(paperId).subscribe((blob) =>
      this.triggerDownload(blob, `paper_${paperId}_markdown.zip`),
    );
  }

  downloadJson(paperId: number): void {
    this.doi.exportJson(paperId).subscribe((blob) =>
      this.triggerDownload(blob, `paper_${paperId}.json`),
    );
  }

  resetFlow(stepper: MatStepper): void {
    this.doiForm.reset({ doi: '' });
    this.sectionForm.reset({ selectedSections: [] });

    this.lookupState.set('idle');
    this.resultState.set('idle');
    this.lookupErrorMessage.set('');
    this.resultErrorMessage.set('');
    this.resolvedPaper.set(null);
    this.sectionResults.set([]);
    this.tabsVisited.set(new Set([0]));

    stepper.reset();
  }
}
