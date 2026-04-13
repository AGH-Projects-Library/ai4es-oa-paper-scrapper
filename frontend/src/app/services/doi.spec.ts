import { TestBed } from '@angular/core/testing';

import { Doi } from './doi';

describe('Doi', () => {
  let service: Doi;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Doi);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
