import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PrometheusComponent } from './prometheus.component';

describe('PrometheusComponent', () => {
  let component: PrometheusComponent;
  let fixture: ComponentFixture<PrometheusComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PrometheusComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PrometheusComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
