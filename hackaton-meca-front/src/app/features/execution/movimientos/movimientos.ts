import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';

@Component({
  selector: 'app-movimientos',
  imports: [
    CommonModule,
    FormsModule,
    DecimalPipe,
    BoxIconComponent,
    TableModule,
    TagModule,
    ButtonModule,
    InputTextModule,
    SelectModule
  ],
  templateUrl: './movimientos.html',
  styleUrl: './movimientos.scss'
})
export class Movimientos {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly searchQuery = signal<string>('');
  readonly selectedRegion = signal<string>('TODAS');
  readonly selectedFinanciador = signal<string>('TODOS');
  readonly currencyMode = signal<'BOB' | 'USD'>('BOB');

  readonly regionOptions = [
    { label: 'Todas las Regiones', value: 'TODAS' },
    { label: 'La Paz', value: 'La Paz' },
    { label: 'Santa Cruz', value: 'Santa Cruz' },
    { label: 'Cochabamba', value: 'Cochabamba' },
    { label: 'Nacional', value: 'Nacional' }
  ];

  readonly financiadorOptions = [
    { label: 'Todos los Donantes', value: 'TODOS' },
    { label: 'CATALYST 18', value: 'CATALYST 18' },
    { label: 'CEL (Comunidad)', value: 'CEL (Comunidad)' },
    { label: 'KJCF (Fundación)', value: 'KJCF (Fundación)' }
  ];

  readonly movimientos = this.financialService.movimientos;

  readonly movimientosFiltrados = computed(() => {
    let list = this.movimientos();
    const query = this.searchQuery().toLowerCase().trim();
    const reg = this.selectedRegion();
    const fin = this.selectedFinanciador();

    if (reg !== 'TODAS') {
      list = list.filter(m => m.region === reg);
    }
    if (fin !== 'TODOS') {
      list = list.filter(m => m.financiador === fin);
    }
    if (query) {
      list = list.filter(
        m =>
          m.comprobante.toLowerCase().includes(query) ||
          m.beneficiario.toLowerCase().includes(query) ||
          m.concepto.toLowerCase().includes(query) ||
          m.codigoCuenta.toLowerCase().includes(query)
      );
    }

    return list;
  });

  readonly totalFiltradoBob = computed(() =>
    this.movimientosFiltrados().reduce((acc, m) => acc + m.montoBob, 0)
  );

  readonly totalFiltradoUsd = computed(() =>
    this.movimientosFiltrados().reduce((acc, m) => acc + m.montoUsd, 0)
  );
}
