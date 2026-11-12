import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Importador } from './importador';

describe('Importador', () => {
  let component: Importador;
  let fixture: ComponentFixture<Importador>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Importador],
    }).compileComponents();

    fixture = TestBed.createComponent(Importador);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
