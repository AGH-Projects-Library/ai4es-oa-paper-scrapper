import { Component } from '@angular/core';
import { Sidebar } from '../sidebar/sidebar';
import { HeroSection } from '../../sections/hero-section/hero-section';
import { ProjectDescription } from '../../sections/project-description/project-description';
import { PaperList } from '../../sections/paper-list/paper-list';

@Component({
  selector: 'app-main-layout',
  imports: [Sidebar, HeroSection, ProjectDescription, PaperList],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.scss',
})
export class MainLayout {}