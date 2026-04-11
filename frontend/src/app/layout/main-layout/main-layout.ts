import { Component } from '@angular/core';
import { Sidebar } from '../sidebar/sidebar';
import { HeroSection } from '../../sections/hero-section/hero-section';
import { ProjectDescription } from '../../sections/project-description/project-description';

@Component({
  selector: 'app-main-layout',
  imports: [Sidebar, HeroSection, ProjectDescription],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss',
})
export class MainLayout {}