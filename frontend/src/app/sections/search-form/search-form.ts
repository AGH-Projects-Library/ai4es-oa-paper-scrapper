import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-search-form',
  imports: [FormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './search-form.html',
  styleUrl: './search-form.scss',
})
export class SearchForm {
  singleDoi = '';
  multipleDois = '';

  clearForm(): void {
    this.singleDoi = '';
    this.multipleDois = '';
  }

  submitForm(): void {
    console.log('Single DOI:', this.singleDoi);
    console.log('Multiple DOIs:', this.multipleDois);
  }
}