import { Component } from '@angular/core';

@Component({
  selector: 'app-sidebar',
  imports: [],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss',
})
export class Sidebar {
  navItems = [
    { label: 'Navigation button', href: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' },
  ];
}