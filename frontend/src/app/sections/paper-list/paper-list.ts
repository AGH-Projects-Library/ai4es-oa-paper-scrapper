import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Doi } from '../../services/doi';
import { PaperSelectionService } from '../../services/paper-selection.service';
import { ApiRequestError } from '../../models/api-error.model';
import { PaperListItem } from '../../models/paper.model';

type LoadState = 'idle' | 'loading' | 'success' | 'error';

@Component({
  selector: 'app-paper-list',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './paper-list.html',
  styleUrl: './paper-list.scss',
})
export class PaperList implements OnInit {
  private readonly doi = inject(Doi);
  private readonly selectionService = inject(PaperSelectionService);

  readonly loadState = signal<LoadState>('idle');
  readonly papers = signal<PaperListItem[]>([]);
  readonly errorMessage = signal('');

  ngOnInit(): void {
    this.loadState.set('loading');
    this.doi.getPapers().subscribe({
      next: (res) => {
        this.papers.set(res.papers);
        this.loadState.set('success');
      },
      error: (err: unknown) => {
        this.errorMessage.set(
          err instanceof ApiRequestError ? err.message : 'Could not load papers.',
        );
        this.loadState.set('error');
      },
    });
  }

  selectPaper(doi: string): void {
    this.selectionService.select(doi);
    document.querySelector('#top')?.scrollIntoView({ behavior: 'smooth' });
  }

  formatAuthors(authors: string[]): string {
    if (authors.length === 0) return 'No authors listed';
    if (authors.length <= 2) return authors.join(', ');
    return `${authors[0]}, ${authors[1]} et al.`;
  }

  formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }
}
