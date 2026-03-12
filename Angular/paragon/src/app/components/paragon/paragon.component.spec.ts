import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ParagonComponent } from './paragon.component';

describe('ParagonComponent', () => {
  let component: ParagonComponent;
  let fixture: ComponentFixture<ParagonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ParagonComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ParagonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
