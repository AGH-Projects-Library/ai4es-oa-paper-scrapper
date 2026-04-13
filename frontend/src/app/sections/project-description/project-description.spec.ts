import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProjectDescription } from './project-description';

describe('ProjectDescription', () => {
  let component: ProjectDescription;
  let fixture: ComponentFixture<ProjectDescription>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProjectDescription],
    }).compileComponents();

    fixture = TestBed.createComponent(ProjectDescription);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
