import { Component } from '@angular/core';

@Component({
  selector: 'app-sidebar',
  imports: [],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss',
})
export class Sidebar {
  navItems = [
    { label: 'Extract paper',    href: '#top' },
    { label: 'Processed papers', href: '#papers' },
    { label: 'About',            href: '#description' },
  ];
}