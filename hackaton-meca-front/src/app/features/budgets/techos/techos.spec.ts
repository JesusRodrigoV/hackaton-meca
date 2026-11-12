import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Techos } from './techos';

describe('Techos', () => {
  let component: Techos;
  let fixture: ComponentFixture<Techos>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Techos],
    }).compileComponents();

    fixture = TestBed.createComponent(Techos);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
