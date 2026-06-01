import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class PaperSelectionService {
  readonly pendingDoi = signal<string | null>(null);

  select(doi: string): void {
    this.pendingDoi.set(doi);
  }

  clear(): void {
    this.pendingDoi.set(null);
  }
}
