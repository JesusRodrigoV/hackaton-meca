import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';

@Component({
  selector: 'app-movimientos',
  imports: [CommonModule, FormsModule, DecimalPipe, BoxIconComponent],
  templateUrl: './movimientos.html',
  styleUrl: './movimientos.scss'
})
export class Movimientos implements OnInit {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  ngOnInit(): void {
    this.financialService.cargarMovimientosApi();
  }

  readonly searchQuery = signal<string>('');
  readonly selectedRegion = signal<string>('TODAS');
  readonly selectedFinanciador = signal<string>('TODOS');
  readonly currencyMode = signal<'BOB' | 'USD'>('BOB');

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
