// Source: notebooks/to_json.ipynb — batch processing loop + file-reading pattern
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Doi } from '../../services/doi';
import { ApiRequestError } from '../../models/api-error.model';
import { BatchResult } from '../../models/paper.model';

type BatchState = 'idle' | 'loading' | 'success' | 'error';
type InputMode = 'text' | 'file';

@Component({
  selector: 'app-batch-processor',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatIconModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './batch-processor.html',
  styleUrl: './batch-processor.scss',
})
export class BatchProcessor {
  private readonly doi = inject(Doi);

  readonly inputMode = signal<InputMode>('text');
  readonly doiText = signal('');
  readonly selectedFile = signal<File | null>(null);
  readonly batchState = signal<BatchState>('idle');
  readonly batchResults = signal<BatchResult[]>([]);
  readonly summary = signal<{ total: number; success: number; not_found: number; error: number } | null>(null);
  readonly errorMessage = signal('');

  setInputMode(mode: InputMode): void {
    this.inputMode.set(mode);
    this.reset();
  }

  onDoiTextChange(value: string): void {
    this.doiText.set(value);
  }

  onFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile.set(input.files?.[0] ?? null);
  }

  canSubmit(): boolean {
    if (this.batchState() === 'loading') return false;
    if (this.inputMode() === 'text') return this.doiText().trim().length > 0;
    return this.selectedFile() !== null;
  }

  submit(): void {
    this.batchState.set('loading');
    this.batchResults.set([]);
    this.summary.set(null);
    this.errorMessage.set('');

    const obs = this.inputMode() === 'text'
      ? this.doi.batchProcess(
          this.doiText().split('\n')
            .map((l) => l.trim())
            .filter((l) => l && !l.startsWith('#')),
        )
      : this.doi.batchProcessUpload(this.selectedFile()!);

    obs.subscribe({
      next: (res) => {
        this.batchResults.set(res.results);
        this.summary.set(res.summary);
        this.batchState.set('success');
      },
      error: (err: unknown) => {
        this.errorMessage.set(
          err instanceof ApiRequestError ? err.message : 'Batch processing failed.',
        );
        this.batchState.set('error');
      },
    });
  }

  reset(): void {
    this.batchState.set('idle');
    this.batchResults.set([]);
    this.summary.set(null);
    this.errorMessage.set('');
    this.doiText.set('');
    this.selectedFile.set(null);
  }
}
