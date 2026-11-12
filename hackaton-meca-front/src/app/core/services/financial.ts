import { Injectable, signal, computed } from '@angular/core';
import {
  PresupuestoTecho,
  MovimientoGasto,
  ModificacionPresupuestaria,
  ImportacionLote,
  KpiSummary,
  AuditItem
} from '../models/financial';

@Injectable({
  providedIn: 'root'
})
export class FinancialService {
  // Techos Presupuestarios reactivos
  private readonly _techos = signal<PresupuestoTecho[]>([
    {
      id: 1,
      codigoCuenta: '5.1.01',
      nombreCuenta: 'Sueldos y Cargas Sociales Profesores',
      rubro: 'Recursos Humanos',
      region: 'La Paz',
      area: 'Formación y Liderazgo',
      financiador: 'CATALYST 18',
      montoInicialBob: 280000,
      modificacionesBob: 20000,
      montoVigenteBob: 300000,
      montoEjecutadoBob: 215450,
      saldoDisponibleBob: 84550,
      porcentajeEjecucion: 71.8,
      estado: 'OK'
    },
    {
      id: 2,
      codigoCuenta: '5.1.02',
      nombreCuenta: 'Honorarios Asesores Pedagógicos',
      rubro: 'Servicios Profesionales',
      region: 'Santa Cruz',
      area: 'Formación y Liderazgo',
      financiador: 'CEL (Comunidad)',
      montoInicialBob: 120000,
      modificacionesBob: -15000,
      montoVigenteBob: 105000,
      montoEjecutadoBob: 112300,
      saldoDisponibleBob: -7300,
      porcentajeEjecucion: 106.9,
      estado: 'SOBREEJECUCION'
    },
    {
      id: 3,
      codigoCuenta: '5.2.03',
      nombreCuenta: 'Talleres Presenciales e Inducción',
      rubro: 'Capacitación y Eventos',
      region: 'Cochabamba',
      area: 'Expansión e Impacto',
      financiador: 'KJCF (Fundación)',
      montoInicialBob: 85000,
      modificacionesBob: 5000,
      montoVigenteBob: 90000,
      montoEjecutadoBob: 68400,
      saldoDisponibleBob: 21600,
      porcentajeEjecucion: 76.0,
      estado: 'OK'
    },
    {
      id: 4,
      codigoCuenta: '5.3.01',
      nombreCuenta: 'Pasajes Aéreos y Terrestres',
      rubro: 'Transporte y Viáticos',
      region: 'Nacional',
      area: 'Dirección Ejecutiva',
      financiador: 'CATALYST 18',
      montoInicialBob: 45000,
      modificacionesBob: 0,
      montoVigenteBob: 45000,
      montoEjecutadoBob: 0,
      saldoDisponibleBob: 45000,
      porcentajeEjecucion: 0,
      estado: 'SIN_EJECUCION'
    },
    {
      id: 5,
      codigoCuenta: '5.4.02',
      nombreCuenta: 'Licencias de Software y Plataforma LMS',
      rubro: 'Tecnología',
      region: 'Nacional',
      area: 'Operaciones y Finanzas',
      financiador: 'CEL (Comunidad)',
      montoInicialBob: 32000,
      modificacionesBob: 8000,
      montoVigenteBob: 40000,
      montoEjecutadoBob: 38900,
      saldoDisponibleBob: 1100,
      porcentajeEjecucion: 97.2,
      estado: 'OK'
    },
    {
      id: 6,
      codigoCuenta: '5.5.01',
      nombreCuenta: 'Gastos Notariales y Legal Registro',
      rubro: 'Servicios Básicos y Legales',
      region: 'La Paz',
      area: 'Dirección Ejecutiva',
      financiador: 'KJCF (Fundación)',
      montoInicialBob: 0,
      modificacionesBob: 0,
      montoVigenteBob: 0,
      montoEjecutadoBob: 4850,
      saldoDisponibleBob: -4850,
      porcentajeEjecucion: 100,
      estado: 'EJEC_SIN_PRESUP'
    }
  ]);

  // Movimientos y Gastos Contables
  private readonly _movimientos = signal<MovimientoGasto[]>([
    {
      id: 101,
      fecha: '2026-03-28',
      comprobante: 'EGR-2026-00341',
      beneficiario: 'Consultora Educativa Andina SRL',
      concepto: 'Pago mensual módulo mentoría pedagógica marzo',
      moneda: 'BOB',
      tipoCambio: 6.96,
      montoBob: 18500,
      montoUsd: 2658.05,
      codigoCuenta: '5.1.02',
      nombreCuenta: 'Honorarios Asesores Pedagógicos',
      region: 'Santa Cruz',
      area: 'Formación y Liderazgo',
      financiador: 'CEL (Comunidad)',
      loteImportacion: 'IMP-2026-03-L1.xlsx',
      auditHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
    },
    {
      id: 102,
      fecha: '2026-03-25',
      comprobante: 'EGR-2026-00338',
      beneficiario: 'Hotel Cochabamba Centro',
      concepto: 'Alquiler salón y refrigerio Bootcamp Nuevos Becarios',
      moneda: 'BOB',
      tipoCambio: 6.96,
      montoBob: 12400,
      montoUsd: 1781.61,
      codigoCuenta: '5.2.03',
      nombreCuenta: 'Talleres Presenciales e Inducción',
      region: 'Cochabamba',
      area: 'Expansión e Impacto',
      financiador: 'KJCF (Fundación)',
      loteImportacion: 'IMP-2026-03-L1.xlsx',
      auditHash: '4bf5792adc25ce7eeec8d4e70a7d5b7feee1578903b3e23f129f41a77cad4f83'
    },
    {
      id: 103,
      fecha: '2026-03-20',
      comprobante: 'EGR-2026-00312',
      beneficiario: 'Google Cloud EMEA',
      concepto: 'Suscripción anual almacenamiento y suite educativa',
      moneda: 'USD',
      tipoCambio: 6.96,
      montoBob: 13920,
      montoUsd: 2000.00,
      codigoCuenta: '5.4.02',
      nombreCuenta: 'Licencias de Software y Plataforma LMS',
      region: 'Nacional',
      area: 'Operaciones y Finanzas',
      financiador: 'CEL (Comunidad)',
      loteImportacion: 'IMP-2026-02-L2.xlsx',
      auditHash: '7d5771c603dda7e44a04d55d7f5752b0f4ef937517a61d15eb0f3b4329241957'
    },
    {
      id: 104,
      fecha: '2026-03-15',
      comprobante: 'EGR-2026-00295',
      beneficiario: 'Notaría de Fe Pública Nº 4',
      concepto: 'Poderes de representación y actualización personerías',
      moneda: 'BOB',
      tipoCambio: 6.96,
      montoBob: 4850,
      montoUsd: 696.84,
      codigoCuenta: '5.5.01',
      nombreCuenta: 'Gastos Notariales y Legal Registro',
      region: 'La Paz',
      area: 'Dirección Ejecutiva',
      financiador: 'KJCF (Fundación)',
      loteImportacion: 'IMP-2026-03-L1.xlsx',
      auditHash: 'a12f3bc8e0984a1e9483021f1532f8319ad0809b1f074ef2f7b764bbd908aa12'
    }
  ]);

  // Modificaciones presupuestarias (traspasos / adiciones)
  private readonly _modificaciones = signal<ModificacionPresupuestaria[]>([
    {
      id: 201,
      fecha: '2026-02-14',
      tipo: 'TRASPASO',
      descripcion: 'Reasignación de honorarios asesores para reforzar sueldos docentes',
      cuentaOrigen: '5.1.02 - Honorarios Asesores Pedagógicos',
      cuentaDestino: '5.1.01 - Sueldos y Cargas Sociales Profesores',
      montoBob: 15000,
      estado: 'APROBADO',
      solicitante: 'Carlos Rojas (Finanzas)',
      aprobador: 'Ana Morales (Director General)'
    },
    {
      id: 202,
      fecha: '2026-03-01',
      tipo: 'INCREMENTO',
      descripcion: 'Ampliación partida LMS por integración con nueva plataforma de evaluación',
      cuentaDestino: '5.4.02 - Licencias de Software y Plataforma LMS',
      montoBob: 8000,
      estado: 'APROBADO',
      solicitante: 'Carlos Rojas (Finanzas)',
      aprobador: 'Ana Morales (Director General)'
    },
    {
      id: 203,
      fecha: '2026-03-24',
      tipo: 'TRASPASO',
      descripcion: 'Solicitud traspaso viáticos hacia talleres de expansión presenciales',
      cuentaOrigen: '5.3.01 - Pasajes Aéreos y Terrestres',
      cuentaDestino: '5.2.03 - Talleres Presenciales e Inducción',
      montoBob: 5000,
      estado: 'BORRADOR',
      solicitante: 'Mariana Paz (Coord. SCZ)'
    }
  ]);

  // Lotes de Importación Excel
  private readonly _importaciones = signal<ImportacionLote[]>([
    {
      id: 1,
      nombreArchivo: 'MAYOR_CONTABLE_2026_Q1.xlsx',
      fecha: '2026-03-29 10:15',
      registrosTotal: 342,
      registrosExitosos: 342,
      registrosError: 0,
      montoTotalBob: 439900,
      estado: 'CONFIRMADO',
      usuario: 'carlos.rojas',
      checksumSha256: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
    },
    {
      id: 2,
      nombreArchivo: 'GASTOS_CAMPO_SANTA_CRUZ_MARZO.xlsx',
      fecha: '2026-03-28 16:40',
      registrosTotal: 58,
      registrosExitosos: 56,
      registrosError: 2,
      montoTotalBob: 32450,
      estado: 'PROCESADO',
      usuario: 'mariana.paz',
      checksumSha256: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
    }
  ]);

  // Auditoría criptográfica (SHA-256 chain)
  private readonly _auditLogs = signal<AuditItem[]>([
    {
      id: 1,
      timestamp: '2026-03-29 10:15:32',
      usuario: 'carlos.rojas',
      accion: 'IMPORT',
      tabla: 'movimientos',
      entidadId: 'Lote #1 (342 registros)',
      detalles: 'Ingesta exitosa archivo MAYOR_CONTABLE_2026_Q1.xlsx',
      hashPrevio: '0000000000000000000000000000000000000000000000000000000000000000',
      hashActual: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      verificado: true
    },
    {
      id: 2,
      timestamp: '2026-03-24 14:22:10',
      usuario: 'mariana.paz',
      accion: 'CREATE',
      tabla: 'presupuesto_modificaciones',
      entidadId: 'MOD-203',
      detalles: 'Solicitud de traspaso presupuestario BOB 5,000',
      hashPrevio: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
      hashActual: 'b3f12456e9c402179a0d81023d53a94821ae3102c9a1038b72e10589a0b12984',
      verificado: true
    },
    {
      id: 3,
      timestamp: '2026-03-01 09:00:15',
      usuario: 'ana.morales',
      accion: 'APPROVE',
      tabla: 'presupuesto_modificaciones',
      entidadId: 'MOD-202',
      detalles: 'Aprobación de incremento BOB 8,000 para partida LMS',
      hashPrevio: 'b3f12456e9c402179a0d81023d53a94821ae3102c9a1038b72e10589a0b12984',
      hashActual: '4a87b1c3e0984a1e9483021f1532f8319ad0809b1f074ef2f7b764bbd908aa99',
      verificado: true
    }
  ]);

  // Readonly accessors
  readonly techos = this._techos.asReadonly();
  readonly movimientos = this._movimientos.asReadonly();
  readonly modificaciones = this._modificaciones.asReadonly();
  readonly importaciones = this._importaciones.asReadonly();
  readonly auditLogs = this._auditLogs.asReadonly();

  // KPIs calculados reactivamente
  readonly kpis = computed<KpiSummary>(() => {
    const list = this._techos();
    const vig = list.reduce((acc, t) => acc + t.montoVigenteBob, 0);
    const ejec = list.reduce((acc, t) => acc + t.montoEjecutadoBob, 0);
    const saldo = vig - ejec;
    const pct = vig > 0 ? (ejec / vig) * 100 : 0;

    return {
      presupuestoVigenteBob: vig,
      ejecutadoBob: ejec,
      saldoDisponibleBob: saldo,
      porcentajeEjecucion: Number(pct.toFixed(1)),
      totalMovimientos: this._movimientos().length,
      cuentasSobreejecutadas: list.filter(t => t.estado === 'SOBREEJECUCION' || t.estado === 'EJEC_SIN_PRESUP').length,
      cuentasEnAlerta: list.filter(t => t.porcentajeEjecucion > 90 && t.porcentajeEjecucion <= 100).length,
      cuentasSinEjecucion: list.filter(t => t.estado === 'SIN_EJECUCION').length
    };
  });

  // Acciones de negocio
  agregarModificacion(mod: Omit<ModificacionPresupuestaria, 'id' | 'fecha' | 'estado'>): void {
    const nuevo: ModificacionPresupuestaria = {
      ...mod,
      id: Date.now(),
      fecha: new Date().toISOString().split('T')[0],
      estado: 'BORRADOR'
    };
    this._modificaciones.update(list => [nuevo, ...list]);
  }

  aprobarModificacion(id: number, aprobadorNombre: string): void {
    this._modificaciones.update(list =>
      list.map(m => m.id === id ? { ...m, estado: 'APROBADO', aprobador: aprobadorNombre } : m)
    );
  }

  revertirLote(loteId: number): void {
    this._importaciones.update(list =>
      list.map(imp => imp.id === loteId ? { ...imp, estado: 'REVERTIDO' } : imp)
    );
  }
}
