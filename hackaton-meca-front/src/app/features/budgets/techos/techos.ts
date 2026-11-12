import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { PresupuestoTecho } from '../../../core/models/financial';

@Component({
  selector: 'app-techos',
  imports: [CommonModule, FormsModule, RouterLink, DecimalPipe, BoxIconComponent],
  templateUrl: './techos.html',
  styleUrl: './techos.scss'
})
export class Techos implements OnInit {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  ngOnInit(): void {
    this.financialService.cargarTechosApi();
  }

  readonly searchQuery = signal<string>('');
  readonly selectedRegion = signal<string>('TODAS');
  readonly selectedFinanciador = signal<string>('TODOS');
  readonly selectedEstado = signal<string>('TODOS');

  readonly techos = this.financialService.techos;

  readonly techosFiltrados = computed(() => {
    let list = this.techos();
    const query = this.searchQuery().toLowerCase().trim();
    const reg = this.selectedRegion();
    const fin = this.selectedFinanciador();
    const est = this.selectedEstado();

    // Filtro por Scope de usuario si no es ADMIN ni FINANCE
    const currentUser = this.authService.currentUser();
    if (currentUser && currentUser.scopeType === 'region') {
      list = list.filter(t => currentUser.scopeLabel.toLowerCase().includes(t.region.toLowerCase()));
    } else if (currentUser && currentUser.scopeType === 'financier') {
      list = list.filter(t => currentUser.scopeLabel.toLowerCase().includes(t.financiador.toLowerCase()));
    }

    if (reg !== 'TODAS') {
      list = list.filter(t => t.region === reg);
    }
    if (fin !== 'TODOS') {
      list = list.filter(t => t.financiador === fin);
    }
    if (est !== 'TODOS') {
      list = list.filter(t => t.estado === est);
    }
    if (query) {
      list = list.filter(
        t =>
          t.codigoCuenta.toLowerCase().includes(query) ||
          t.nombreCuenta.toLowerCase().includes(query) ||
          t.rubro.toLowerCase().includes(query) ||
          t.area.toLowerCase().includes(query)
      );
    }

    return list;
  });

  // Totales de la selección actual
  readonly totalVigente = computed(() =>
    this.techosFiltrados().reduce((acc, t) => acc + t.montoVigenteBob, 0)
  );

  readonly totalEjecutado = computed(() =>
    this.techosFiltrados().reduce((acc, t) => acc + t.montoEjecutadoBob, 0)
  );

  readonly totalSaldo = computed(() =>
    this.totalVigente() - this.totalEjecutado()
  );

  readonly porcentajeGlobal = computed(() => {
    const vig = this.totalVigente();
    return vig > 0 ? Number(((this.totalEjecutado() / vig) * 100).toFixed(1)) : 0;
  });

  exportarCsv(): void {
    const data = this.techosFiltrados();
    const headers = [
      'Código',
      'Cuenta',
      'Rubro',
      'Región',
      'Área',
      'Financiador',
      'Inicial BOB',
      'Modificaciones BOB',
      'Vigente BOB',
      'Ejecutado BOB',
      'Saldo BOB',
      '% Ejecución',
      'Estado'
    ];

    const rows = data.map(t => [
      t.codigoCuenta,
      `"${t.nombreCuenta}"`,
      `"${t.rubro}"`,
      t.region,
      `"${t.area}"`,
      `"${t.financiador}"`,
      t.montoInicialBob,
      t.modificacionesBob,
      t.montoVigenteBob,
      t.montoEjecutadoBob,
      t.saldoDisponibleBob,
      t.porcentajeEjecucion,
      t.estado
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,\uFEFF' +
      [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `Techos_Presupuestarios_${this.authService.currentGestion()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
