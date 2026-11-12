import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Modificaciones } from './modificaciones';

describe('Modificaciones', () => {
  let component: Modificaciones;
  let fixture: ComponentFixture<Modificaciones>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Modificaciones],
    }).compileComponents();

    fixture = TestBed.createComponent(Modificaciones);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
