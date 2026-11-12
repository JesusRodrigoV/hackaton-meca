import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';

@Component({
  selector: 'app-techos',
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    DecimalPipe,
    BoxIconComponent,
    TableModule,
    TagModule,
    ButtonModule,
    InputTextModule,
    SelectModule
  ],
  templateUrl: './techos.html',
  styleUrl: './techos.scss'
})
export class Techos {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly searchQuery = signal<string>('');
  readonly selectedRegion = signal<string>('TODAS');
  readonly selectedFinanciador = signal<string>('TODOS');
  readonly selectedEstado = signal<string>('TODOS');

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

  readonly estadoOptions = [
    { label: 'Todos los Estados', value: 'TODOS' },
    { label: 'OK (En norma)', value: 'OK' },
    { label: 'Sobreejecución', value: 'SOBREEJECUCION' },
    { label: 'Sin Ejecución', value: 'SIN_EJECUCION' },
    { label: 'Sin Techo Previo', value: 'EJEC_SIN_PRESUP' }
  ];

  readonly techos = this.financialService.techos;

  readonly techosFiltrados = computed(() => {
    let list = this.techos();
    const query = this.searchQuery().toLowerCase().trim();
    const reg = this.selectedRegion();
    const fin = this.selectedFinanciador();
    const est = this.selectedEstado();

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

  getEstadoSeverity(estado: string): 'success' | 'danger' | 'secondary' | 'warn' {
    switch (estado) {
      case 'OK': return 'success';
      case 'SOBREEJECUCION':
      case 'EJEC_SIN_PRESUP': return 'danger';
      case 'SIN_EJECUCION': return 'secondary';
      default: return 'warn';
    }
  }

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
    link.setAttribute('download', `Presupuesto_Anual_${this.authService.currentGestion()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
