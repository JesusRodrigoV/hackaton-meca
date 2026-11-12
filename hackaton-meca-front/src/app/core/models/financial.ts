export type EstadoEjecucion = 'OK' | 'SOBREEJECUCION' | 'SIN_EJECUCION' | 'EJEC_SIN_PRESUP';

export interface PresupuestoTecho {
  id: number;
  codigoCuenta: string;
  nombreCuenta: string;
  rubro: string;
  region: string;
  area: string;
  financiador: string;
  montoInicialBob: number;
  modificacionesBob: number;
  montoVigenteBob: number;
  montoEjecutadoBob: number;
  saldoDisponibleBob: number;
  porcentajeEjecucion: number;
  estado: EstadoEjecucion;
}

export interface MovimientoGasto {
  id: number;
  fecha: string;
  comprobante: string;
  beneficiario: string;
  concepto: string;
  moneda: 'BOB' | 'USD';
  tipoCambio: number;
  montoBob: number;
  montoUsd: number;
  codigoCuenta: string;
  nombreCuenta: string;
  region: string;
  area: string;
  financiador: string;
  loteImportacion?: string;
  auditHash: string;
}

export interface ModificacionPresupuestaria {
  id: number;
  fecha: string;
  tipo: 'TRASPASO' | 'INCREMENTO' | 'DISMINUCION';
  descripcion: string;
  cuentaOrigen?: string;
  cuentaDestino?: string;
  montoBob: number;
  estado: 'BORRADOR' | 'APROBADO' | 'RECHAZADO';
  solicitante: string;
  aprobador?: string;
}

export interface ImportacionLote {
  id: number;
  nombreArchivo: string;
  fecha: string;
  registrosTotal: number;
  registrosExitosos: number;
  registrosError: number;
  montoTotalBob: number;
  estado: 'PROCESADO' | 'CONFIRMADO' | 'REVERTIDO';
  usuario: string;
  checksumSha256: string;
}

export interface KpiSummary {
  presupuestoVigenteBob: number;
  ejecutadoBob: number;
  saldoDisponibleBob: number;
  porcentajeEjecucion: number;
  totalMovimientos: number;
  cuentasSobreejecutadas: number;
  cuentasEnAlerta: number;
  cuentasSinEjecucion: number;
}

export interface ReportFilter {
  gestion: number;
  region: string;
  financiador: string;
  area: string;
  mesDesde?: number;
  mesHasta?: number;
  search?: string;
}

export interface AuditItem {
  id: number;
  timestamp: string;
  usuario: string;
  accion: 'CREATE' | 'UPDATE' | 'IMPORT' | 'APPROVE' | 'REVERT';
  tabla: string;
  entidadId: number | string;
  detalles: string;
  hashPrevio: string;
  hashActual: string;
  verificado: boolean;
}
