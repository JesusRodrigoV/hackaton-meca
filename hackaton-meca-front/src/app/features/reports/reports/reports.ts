import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';

export type TipoReporte = 'REP-01' | 'REP-02' | 'REP-03' | 'REP-04' | 'REP-05' | 'REP-06' | 'REP-07';

@Component({
  selector: 'app-reports',
  imports: [
    CommonModule,
    FormsModule,
    DecimalPipe,
    BoxIconComponent,
    TableModule,
    TagModule,
    ButtonModule,
    SelectModule
  ],
  templateUrl: './reports.html',
  styleUrl: './reports.scss'
})
export class Reports {
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly activeTab = signal<TipoReporte>('REP-01');
  readonly moneda = signal<'BOB' | 'USD'>('BOB');

  readonly gestionOptions = [
    { label: 'Gestión 2026 (En Curso)', value: 2026 },
    { label: 'Gestión 2025 (Cerrada)', value: 2025 },
    { label: 'Gestión 2024 (Histórica)', value: 2024 }
  ];

  readonly monedaOptions = [
    { label: 'Bolivianos (BOB)', value: 'BOB' },
    { label: 'Dólares Americanos (USD)', value: 'USD' }
  ];

  readonly techos = this.financialService.techos;
  readonly movimientos = this.financialService.movimientos;
  readonly auditLogs = this.financialService.auditLogs;

  readonly reportTabs = [
    { id: 'REP-01' as const, code: 'REP-01', title: 'Ejecución vs Techos' },
    { id: 'REP-02' as const, code: 'REP-02', title: 'Por Donante' },
    { id: 'REP-03' as const, code: 'REP-03', title: 'Por Región' },
    { id: 'REP-04' as const, code: 'REP-04', title: 'Por Área' },
    { id: 'REP-05' as const, code: 'REP-05', title: 'Flujo Mensual' },
    { id: 'REP-06' as const, code: 'REP-06', title: 'Partidas con Sobregiro' },
    { id: 'REP-07' as const, code: 'REP-07', title: 'Registro de Auditoría' }
  ];

  readonly reportePorFinanciador = computed(() => {
    const map = new Map<string, { inicial: number; modif: number; vigente: number; ejecutado: number; saldo: number }>();
    for (const t of this.techos()) {
      const cur = map.get(t.financiador) || { inicial: 0, modif: 0, vigente: 0, ejecutado: 0, saldo: 0 };
      cur.inicial += t.montoInicialBob;
      cur.modif += t.modificacionesBob;
      cur.vigente += t.montoVigenteBob;
      cur.ejecutado += t.montoEjecutadoBob;
      cur.saldo += t.saldoDisponibleBob;
      map.set(t.financiador, cur);
    }
    return Array.from(map.entries()).map(([nombre, vals]) => ({
      nombre,
      ...vals,
      pct: vals.vigente > 0 ? Number(((vals.ejecutado / vals.vigente) * 100).toFixed(1)) : 0
    }));
  });

  readonly reportePorRegion = computed(() => {
    const map = new Map<string, { inicial: number; vigente: number; ejecutado: number; saldo: number }>();
    for (const t of this.techos()) {
      const cur = map.get(t.region) || { inicial: 0, vigente: 0, ejecutado: 0, saldo: 0 };
      cur.inicial += t.montoInicialBob;
      cur.vigente += t.montoVigenteBob;
      cur.ejecutado += t.montoEjecutadoBob;
      cur.saldo += t.saldoDisponibleBob;
      map.set(t.region, cur);
    }
    return Array.from(map.entries()).map(([nombre, vals]) => ({
      nombre,
      ...vals,
      pct: vals.vigente > 0 ? Number(((vals.ejecutado / vals.vigente) * 100).toFixed(1)) : 0
    }));
  });

  readonly reportePorArea = computed(() => {
    const map = new Map<string, { vigente: number; ejecutado: number; saldo: number }>();
    for (const t of this.techos()) {
      const cur = map.get(t.area) || { vigente: 0, ejecutado: 0, saldo: 0 };
      cur.vigente += t.montoVigenteBob;
      cur.ejecutado += t.montoEjecutadoBob;
      cur.saldo += t.saldoDisponibleBob;
      map.set(t.area, cur);
    }
    return Array.from(map.entries()).map(([nombre, vals]) => ({
      nombre,
      ...vals,
      pct: vals.vigente > 0 ? Number(((vals.ejecutado / vals.vigente) * 100).toFixed(1)) : 0
    }));
  });

  readonly reporteDesviaciones = computed(() => {
    return this.techos().filter(t => t.estado === 'SOBREEJECUCION' || t.estado === 'EJEC_SIN_PRESUP' || t.porcentajeEjecucion >= 90);
  });

  exportarReporteActual(): void {
    const tab = this.reportTabs.find(t => t.id === this.activeTab());
    alert(`Exportando ${tab?.code} - ${tab?.title} a formato Excel.`);
  }

  imprimirReporte(): void {
    window.print();
  }
}
