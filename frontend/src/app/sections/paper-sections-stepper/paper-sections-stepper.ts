import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatStepper, MatStepperModule } from '@angular/material/stepper';

type LookupState = 'idle' | 'loading' | 'success' | 'not_found' | 'service_error';
type ResultState = 'idle' | 'loading' | 'success' | 'error';

interface PaperSection {
  id: string;
  name: string;
}

interface ResolvedPaper {
  doi: string;
  title: string;
  authors: string[];
  source: string;
  year: number | null;
  availableSections: PaperSection[];
}

interface SectionResult {
  id: string;
  name: string;
  content: string;
}

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
  ],
  templateUrl: './paper-sections-stepper.html',
  styleUrl: './paper-sections-stepper.scss',
})
export class PaperSectionsStepper {
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

  constructor(private fb: FormBuilder) {
    this.doiForm = this.fb.nonNullable.group({
      doi: this.fb.nonNullable.control('', [
        Validators.required,
        Validators.pattern(/^10\.\S+\/\S+$/),
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
      if (!current.includes(sectionId)) {
        this.selectedSectionsControl.setValue([...current, sectionId]);
      }
    } else {
      this.selectedSectionsControl.setValue(
        current.filter((id) => id !== sectionId)
      );
    }

    this.selectedSectionsControl.markAsTouched();
    this.selectedSectionsControl.updateValueAndValidity();
  }

  lookupPaper(stepper: MatStepper): void {
    this.doiForm.markAllAsTouched();

    if (this.doiForm.invalid) {
      return;
    }

    const normalizedDoi = this.normalizeDoi(this.doiControl.value);
    this.doiControl.setValue(normalizedDoi);

    this.lookupState.set('loading');
    this.lookupErrorMessage.set('');
    this.resultState.set('idle');
    this.resultErrorMessage.set('');
    this.resolvedPaper.set(null);
    this.sectionResults.set([]);
    this.sectionForm.reset({ selectedSections: [] });

    setTimeout(() => {
      if (normalizedDoi === '10.0000/notfound') {
        this.lookupState.set('not_found');
        this.lookupErrorMessage.set(
          'We couldn’t find a paper for this DOI. Please check the DOI and try again.'
        );
        return;
      }

      if (normalizedDoi === '10.0000/error') {
        this.lookupState.set('service_error');
        this.lookupErrorMessage.set(
          'We couldn’t connect to the lookup service. Please try again.'
        );
        return;
      }

      this.resolvedPaper.set({
        doi: normalizedDoi,
        title:
          'Automated Extraction of Sections from Open-Access Research Papers',
        authors: ['Natalia Kowalska', 'Alice Smith', 'Jan Nowak'],
        source: 'PubMed Central',
        year: 2025,
        availableSections: [
          { id: 'abstract', name: 'Abstract' },
          { id: 'introduction', name: 'Introduction' },
          { id: 'methods', name: 'Methods' },
          { id: 'results', name: 'Results' },
          { id: 'discussion', name: 'Discussion' },
          { id: 'conclusion', name: 'Conclusion' },
        ],
      });

      this.lookupState.set('success');
      stepper.next();
    }, 1200);
  }

  fetchSelectedSections(stepper: MatStepper): void {
    this.sectionForm.markAllAsTouched();

    if (this.sectionForm.invalid || !this.resolvedPaper()) {
      return;
    }

    this.resultState.set('loading');
    this.resultErrorMessage.set('');
    this.sectionResults.set([]);
    stepper.next();

    const paper = this.resolvedPaper();
    const selectedIds = this.selectedSectionsControl.value;

    setTimeout(() => {
      if (!paper) {
        this.resultState.set('error');
        this.resultErrorMessage.set(
          'We couldn’t load the selected sections because no paper data is available.'
        );
        return;
      }

      if (paper.doi === '10.0000/sectionerror') {
        this.resultState.set('error');
        this.resultErrorMessage.set(
          'We found the paper, but section retrieval failed. Please try again.'
        );
        return;
      }

      const sectionLibrary: Record<string, string> = {
        abstract:
          'This paper presents a lightweight pipeline for retrieving open-access articles and extracting structured sections from them for downstream research workflows.',
        introduction:
          'The introduction motivates automated evidence synthesis and explains the need for reliable access to well-structured paper content across repositories such as PubMed Central and arXiv.',
        methods:
          'The methods describe how the paper is fetched from its source, converted into a normalized markdown representation, parsed into title and section blocks, and prepared for interactive viewing.',
        results:
          'The results section reports that structured parsing makes it possible to recover major article sections and surface them for selective extraction and review.',
        discussion:
          'The discussion highlights practical limitations, including inconsistent section naming, missing metadata, and structural differences between repositories.',
        conclusion:
          'The conclusion emphasizes that section-based extraction is a useful step toward browser-based tools for literature review and evidence synthesis.',
      };

      const results: SectionResult[] = paper.availableSections
        .filter((section) => selectedIds.includes(section.id))
        .map((section) => ({
          id: section.id,
          name: section.name,
          content:
            sectionLibrary[section.id] ??
            'No content is currently available for this section.',
        }));

      this.sectionResults.set(results);
      this.resultState.set('success');
    }, 1400);
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

    stepper.reset();
  }
}