import { Component, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { PaperSectionsStepper } from '../paper-sections-stepper/paper-sections-stepper';
import { BatchProcessor } from '../batch-processor/batch-processor';

@Component({
  selector: 'app-hero-section',
  imports: [MatButtonModule, MatButtonToggleModule, PaperSectionsStepper, BatchProcessor],
  templateUrl: './hero-section.html',
  styleUrl: './hero-section.scss',
})
export class HeroSection {
  readonly mode = signal<'single' | 'batch'>('single');
}
