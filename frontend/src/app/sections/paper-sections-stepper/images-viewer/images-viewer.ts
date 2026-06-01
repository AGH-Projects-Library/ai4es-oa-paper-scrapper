import { Component, OnInit, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { Doi } from '../../../services/doi';
import { ApiRequestError } from '../../../models/api-error.model';
import { PaperImage } from '../../../models/paper.model';

@Component({
  selector: 'app-images-viewer',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule, MatIconModule],
  templateUrl: './images-viewer.html',
  styleUrl: './images-viewer.scss',
})
export class ImagesViewer implements OnInit {
  readonly paperId = input.required<number>();

  private readonly doi = inject(Doi);

  readonly loadState = signal<'idle' | 'loading' | 'success' | 'error'>('idle');
  readonly images = signal<PaperImage[]>([]);
  readonly errorMessage = signal('');

  ngOnInit(): void {
    this.loadState.set('loading');
    this.doi.getImages(this.paperId()).subscribe({
      next: (res) => {
        this.images.set(res.images);
        this.loadState.set('success');
      },
      error: (err: unknown) => {
        this.errorMessage.set(
          err instanceof ApiRequestError ? err.message : 'Could not load images.',
        );
        this.loadState.set('error');
      },
    });
  }

  imageUrl(idx: number): string {
    return this.doi.imageUrl(this.paperId(), idx);
  }
}
