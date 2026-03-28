import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { SearchForm } from '../search-form/search-form';

@Component({
  selector: 'app-hero-section',
  imports: [MatButtonModule, SearchForm],
  templateUrl: './hero-section.html',
  styleUrl: './hero-section.scss',
})
export class HeroSection {}