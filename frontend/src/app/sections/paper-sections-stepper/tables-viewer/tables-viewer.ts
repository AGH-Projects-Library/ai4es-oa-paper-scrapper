import { Component, OnInit, inject, input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { Doi } from '../../../services/doi';
import { ApiRequestError } from '../../../models/api-error.model';
import { PaperTableMeta, PaperTableData } from '../../../models/paper.model';

type LoadState = 'idle' | 'loading' | 'success' | 'error';

@Component({
  selector: 'app-tables-viewer',
  standalone: true,
  imports: [CommonModule, MatProgressSpinnerModule, MatIconModule, MatExpansionModule],
  templateUrl: './tables-viewer.html',
  styleUrl: './tables-viewer.scss',
})
export class TablesViewer implements OnInit {
  readonly paperId = input.required<number>();

  private readonly doi = inject(Doi);

  readonly listState = signal<LoadState>('idle');
  readonly tables = signal<PaperTableMeta[]>([]);
  readonly listError = signal('');

  readonly tableData = signal<Map<number, PaperTableData>>(new Map());
  readonly tableLoadState = signal<Map<number, LoadState>>(new Map());
  readonly tableError = signal<Map<number, string>>(new Map());

  ngOnInit(): void {
    this.listState.set('loading');
    this.doi.getTables(this.paperId()).subscribe({
      next: (res) => {
        this.tables.set(res.tables);
        this.listState.set('success');
      },
      error: (err: unknown) => {
        this.listError.set(
          err instanceof ApiRequestError ? err.message : 'Could not load tables.',
        );
        this.listState.set('error');
      },
    });
  }

  loadTableDetail(globalIndex: number): void {
    const stateMap = new Map(this.tableLoadState());
    const current = stateMap.get(globalIndex);
    if (current === 'success' || current === 'loading') return;

    stateMap.set(globalIndex, 'loading');
    this.tableLoadState.set(stateMap);

    this.doi.getTableDetail(this.paperId(), globalIndex).subscribe({
      next: (res) => {
        const dataMap = new Map(this.tableData());
        dataMap.set(globalIndex, res);
        this.tableData.set(dataMap);

        const sm = new Map(this.tableLoadState());
        sm.set(globalIndex, 'success');
        this.tableLoadState.set(sm);
      },
      error: (err: unknown) => {
        const em = new Map(this.tableError());
        em.set(
          globalIndex,
          err instanceof ApiRequestError ? err.message : 'Could not load table data.',
        );
        this.tableError.set(em);

        const sm = new Map(this.tableLoadState());
        sm.set(globalIndex, 'error');
        this.tableLoadState.set(sm);
      },
    });
  }

  getTableState(globalIndex: number): LoadState {
    return this.tableLoadState().get(globalIndex) ?? 'idle';
  }

  getTableData(globalIndex: number): PaperTableData | undefined {
    return this.tableData().get(globalIndex);
  }

  getTableError(globalIndex: number): string {
    return this.tableError().get(globalIndex) ?? '';
  }
}
