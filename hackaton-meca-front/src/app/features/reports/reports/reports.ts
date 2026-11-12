import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { FinancialService } from '../../../core/services/financial';
import { AuthService } from '../../../core/auth/auth';
import { BoxIconComponent } from '../../../shared/components/box-icon/box-icon';
import { API_CONFIG } from '../../../core/config/api.config';

export type TipoReporte = 'REP-01' | 'REP-02' | 'REP-03' | 'REP-04' | 'REP-05' | 'REP-06' | 'REP-07';

@Component({
  selector: 'app-reports',
  imports: [CommonModule, FormsModule, DecimalPipe, BoxIconComponent],
  templateUrl: './reports.html',
  styleUrl: './reports.scss'
})
export class Reports implements OnInit {
  private readonly http = inject(HttpClient, { optional: true });
  readonly financialService = inject(FinancialService);
  readonly authService = inject(AuthService);

  readonly activeTab = signal<TipoReporte>('REP-01');
  readonly moneda = signal<'BOB' | 'USD'>('BOB');
  readonly selectedRegion = signal<string>('TODAS');
  readonly selectedFinanciador = signal<string>('TODOS');

  readonly techos = this.financialService.techos;
  readonly movimientos = this.financialService.movimientos;
  readonly auditLogs = this.financialService.auditLogs;

  // Datos directos de API
  readonly reportesApiFinanciador = signal<any[] | null>(null);
  readonly reportesApiRegion = signal<any[] | null>(null);
  readonly reportesApiArea = signal<any[] | null>(null);
  readonly reportesApiVariaciones = signal<any[] | null>(null);

  async ngOnInit(): Promise<void> {
    await this.financialService.cargarTechosApi();
    await this.financialService.cargarMovimientosApi();
    await this.financialService.cargarAuditoriaApi();

    try {
      const [fin, reg, area, vars] = await Promise.all([
        this.financialService.cargarReporteFinanciadoresApi(),
        this.financialService.cargarReporteRegionesApi(),
        this.financialService.cargarReporteAreasApi(),
        this.financialService.cargarReporteVariacionesApi()
      ]);
      if (fin) this.reportesApiFinanciador.set(fin);
      if (reg) this.reportesApiRegion.set(reg);
      if (area) this.reportesApiArea.set(area);
      if (vars) this.reportesApiVariaciones.set(vars);
    } catch {
      // Computa sobre techos locales
    }
  }

  readonly reportTabs = [
    { id: 'REP-01' as const, title: 'Ejecución General vs Techos', icon: 'file-blank' },
    { id: 'REP-02' as const, title: 'Por Financiador / Donante', icon: 'buildings' },
    { id: 'REP-03' as const, title: 'Por Región Geográfica', icon: 'map' },
    { id: 'REP-04' as const, title: 'Por Área Programática', icon: 'group' },
    { id: 'REP-05' as const, title: 'Flujo Mensual / Trimestral', icon: 'calendar' },
    { id: 'REP-06' as const, title: 'Desviaciones y Alertas', icon: 'alarm-exclamation' },
    { id: 'REP-07' as const, title: 'Trazabilidad SHA-256', icon: 'shield-quarter' }
  ];

  // Reporte 2: Agrupado por Financiador
  readonly reportePorFinanciador = computed(() => {
    const apiData = this.reportesApiFinanciador();
    if (apiData && apiData.length > 0) {
      return apiData.map(r => ({
        nombre: r.financiador,
        inicial: r.inicialBob ?? r.inicial ?? 0,
        modif: r.modificacionesBob ?? r.modificaciones ?? 0,
        vigente: r.vigenteBob ?? r.vigente ?? 0,
        ejecutado: r.ejecutadoBob ?? r.ejecutado ?? 0,
        saldo: r.saldoBob ?? r.saldo ?? 0,
        pct: r.porcentaje ?? 0
      }));
    }

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

  // Reporte 3: Agrupado por Región
  readonly reportePorRegion = computed(() => {
    const apiData = this.reportesApiRegion();
    if (apiData && apiData.length > 0) {
      return apiData.map(r => ({
        nombre: r.region,
        inicial: r.inicialBob ?? r.vigenteBob ?? 0,
        vigente: r.vigenteBob ?? r.vigente ?? 0,
        ejecutado: r.ejecutadoBob ?? r.ejecutado ?? 0,
        saldo: r.saldoBob ?? r.saldo ?? 0,
        pct: r.porcentaje ?? 0
      }));
    }

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

  // Reporte 4: Agrupado por Área
  readonly reportePorArea = computed(() => {
    const apiData = this.reportesApiArea();
    if (apiData && apiData.length > 0) {
      return apiData.map(r => ({
        nombre: r.area,
        vigente: r.vigenteBob ?? r.vigente ?? 0,
        ejecutado: r.ejecutadoBob ?? r.ejecutado ?? 0,
        saldo: r.saldoBob ?? r.saldo ?? 0,
        pct: r.porcentaje ?? 0
      }));
    }

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

  // Reporte 6: Desviaciones y Sobreejecuciones
  readonly reporteDesviaciones = computed(() => {
    const apiData = this.reportesApiVariaciones();
    if (apiData && apiData.length > 0) {
      return apiData.map((v, i) => ({
        id: i + 1,
        codigoCuenta: v.codigo || '5.0.00',
        nombreCuenta: v.partida || 'Partida Presupuestaria',
        rubro: v.rubro || 'General',
        region: 'Nacional',
        area: 'Institucional',
        financiador: v.financiador || 'Todos',
        montoInicialBob: v.vigenteBob,
        modificacionesBob: 0,
        montoVigenteBob: v.vigenteBob,
        montoEjecutadoBob: v.ejecutadoBob,
        saldoDisponibleBob: v.saldoBob,
        porcentajeEjecucion: v.vigenteBob > 0 ? Number(((v.ejecutadoBob / v.vigenteBob) * 100).toFixed(1)) : 0,
        estado: v.alerta || 'SOBREEJECUCION'
      }));
    }
    return this.techos().filter(t => t.estado === 'SOBREEJECUCION' || t.estado === 'EJEC_SIN_PRESUP' || t.porcentajeEjecucion >= 90);
  });

  onReportTabKeydown(event: KeyboardEvent, currentIndex: number): void {
    let nextIndex = currentIndex;

    if (event.key === 'ArrowRight') {
      nextIndex = (currentIndex + 1) % this.reportTabs.length;
    } else if (event.key === 'ArrowLeft') {
      nextIndex = (currentIndex - 1 + this.reportTabs.length) % this.reportTabs.length;
    } else if (event.key === 'Home') {
      nextIndex = 0;
    } else if (event.key === 'End') {
      nextIndex = this.reportTabs.length - 1;
    } else {
      return;
    }

    event.preventDefault();
    this.activeTab.set(this.reportTabs[nextIndex].id);
    const tabList = (event.currentTarget as HTMLElement).closest('[role="tablist"]');
    tabList?.querySelectorAll<HTMLElement>('[role="tab"]')[nextIndex]?.focus();
  }

  private async descargarArchivo(exportUrl: string, nombreArchivo: string): Promise<void> {
    if (this.http) {
      try {
        const blob = await firstValueFrom(this.http.get(exportUrl, { responseType: 'blob' }));
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = nombreArchivo;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        return;
      } catch (err) {
        console.warn('Descarga por HttpClient falló, recurriendo a enlace directo:', err);
      }
    }

    const link = document.createElement('a');
    link.href = exportUrl;
    link.target = '_blank';
    link.download = nombreArchivo;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  private buildExportFilename(ext: 'xlsx' | 'pdf'): string {
    const tab = this.reportTabs.find(t => t.id === this.activeTab());
    const title = (tab?.title ?? 'Ejecucion').replace(/[\s\/]+/g, '_');
    return `Reporte_${title}_${this.moneda()}_${this.authService.currentGestion()}.${ext}`;
  }

  async descargarExcel(): Promise<void> {
    const tipo = this.activeTab();
    const exportUrl = `${API_CONFIG.endpoints.reportes.exportarExcel(tipo)}&moneda=${this.moneda()}`;
    await this.descargarArchivo(exportUrl, this.buildExportFilename('xlsx'));
  }

  async descargarPdf(): Promise<void> {
    const tipo = this.activeTab();
    const exportUrl = `${API_CONFIG.endpoints.reportes.exportarPdf(tipo)}&moneda=${this.moneda()}`;
    await this.descargarArchivo(exportUrl, this.buildExportFilename('pdf'));
  }

  exportarReporteActual(): void {
    this.descargarExcel();
  }

  imprimirReporte(): void {
    this.descargarPdf();
  }
}
