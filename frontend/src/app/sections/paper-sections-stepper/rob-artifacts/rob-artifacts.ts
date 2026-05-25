import { Component, computed, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import {
  RobArtifact,
  RobSectionArtifact,
  RobTableArtifact,
} from '../../../models/paper.model';

@Component({
  selector: 'app-rob-artifacts',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './rob-artifacts.html',
  styleUrl: './rob-artifacts.scss',
})
export class RobArtifacts {
  readonly artifacts = input.required<RobArtifact[]>();

  readonly sectionArtifacts = computed(() =>
    this.artifacts().filter(
      (a): a is RobSectionArtifact => a.artifact_type === 'section',
    ),
  );

  readonly tableArtifacts = computed(() =>
    this.artifacts().filter(
      (a): a is RobTableArtifact =>
        a.artifact_type === 'table' || a.artifact_type === 'ocr_table',
    ),
  );

  confidenceClass(value: number): string {
    if (value >= 0.85) return 'confidence-high';
    if (value >= 0.6) return 'confidence-medium';
    return 'confidence-low';
  }

  confidencePercent(value: number): string {
    return `${Math.round(value * 100)}%`;
  }
}
