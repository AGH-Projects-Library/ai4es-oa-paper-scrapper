import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
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
import { Doi } from '../../services/doi';
import { PaperSection, ResolvedPaper } from '../../models/paper.model';
import { ApiRequestError } from '../../models/api-error.model';

type LookupState = 'idle' | 'loading' | 'success' | 'not_found' | 'service_error';

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
  private readonly fb = inject(FormBuilder);
  private readonly resolveDoiApi = inject(Doi);

  readonly doiForm: FormGroup<{
    doi: FormControl<string>;
  }>;

  readonly sectionForm: FormGroup<{
    selectedSections: FormControl<string[]>;
  }>;

  readonly lookupState = signal<LookupState>('idle');
  readonly lookupErrorMessage = signal('');
  readonly resolvedPaper = signal<ResolvedPaper | null>(null);

  constructor() {
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

  getSelectedSectionObjects(): PaperSection[] {
    const paper = this.resolvedPaper();
    const selectedIds = this.selectedSectionsControl.value;

    if (!paper) {
      return [];
    }

    return paper.availableSections.filter((section) =>
      selectedIds.includes(section.id)
    );
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
    this.resolvedPaper.set(null);
    this.sectionForm.reset({ selectedSections: [] });

    this.resolveDoiApi.resolveDoi({ doi: normalizedDoi }).subscribe({
      next: (response) => {
        if (response.status === 'not_found') {
          this.lookupState.set('not_found');
          this.lookupErrorMessage.set(response.message);
          return;
        }

        this.resolvedPaper.set(response.paper);
        this.lookupState.set('success');
        stepper.next();
      },
      error: (error: ApiRequestError) => {
        this.lookupState.set('service_error');
        this.lookupErrorMessage.set(error.message);
      },
    });
  }

  goToSummary(stepper: MatStepper): void {
    this.sectionForm.markAllAsTouched();

    if (this.sectionForm.invalid) {
      return;
    }

    stepper.next();
  }

  resetFlow(stepper: MatStepper): void {
    this.doiForm.reset({ doi: '' });
    this.sectionForm.reset({ selectedSections: [] });
    this.lookupState.set('idle');
    this.lookupErrorMessage.set('');
    this.resolvedPaper.set(null);
    stepper.reset();
  }
}