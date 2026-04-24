import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { PaperSectionsStepper } from '../paper-sections-stepper/paper-sections-stepper';

@Component({
  selector: 'app-hero-section',
  imports: [MatButtonModule, PaperSectionsStepper],
  templateUrl: './hero-section.html',
  styleUrl: './hero-section.scss',
})
export class HeroSection {}