import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PaperSectionsStepper } from './paper-sections-stepper';

describe('PaperSectionsStepper', () => {
  let component: PaperSectionsStepper;
  let fixture: ComponentFixture<PaperSectionsStepper>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PaperSectionsStepper],
    }).compileComponents();

    fixture = TestBed.createComponent(PaperSectionsStepper);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
