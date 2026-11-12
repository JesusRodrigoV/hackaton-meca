/**
 * Configuración de endpoints y URLs de integración con el backend FastAPI
 */
export const API_CONFIG = {
  baseUrl: '/api/v1',
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      me: '/api/v1/auth/me',
      refresh: '/api/v1/auth/refresh',
      logout: '/api/v1/auth/logout',
      changePassword: '/api/v1/auth/change-password',
      twoFactorStatus: '/api/v1/auth/2fa/status',
      twoFactorSetup: '/api/v1/auth/2fa/setup',
      twoFactorEnable: '/api/v1/auth/2fa/enable',
      twoFactorDisable: '/api/v1/auth/2fa/disable',
      twoFactorVerifyLogin: '/api/v1/auth/2fa/verify-login'
    },
    presupuestos: {
      techos: '/api/v1/presupuestos/techos',
      modificaciones: '/api/v1/presupuestos/modificaciones',
      aprobarModificacion: (id: number) => `/api/v1/presupuestos/modificaciones/${id}/aprobar`,
      resumen: '/api/v1/presupuestos/resumen'
    },
    ejecucion: {
      movimientos: '/api/v1/movements',
      subirPlanilla: '/api/v1/movements/import-excel',
      confirmarLote: (batchId: number) => `/api/v1/movements/batches/${batchId}/confirm`,
      revertirLote: (batchId: number) => `/api/v1/movements/batches/${batchId}`,
      lotes: '/api/v1/movements/batches'
    },
    reportes: {
      ejecucionDonante: '/api/v1/reports/donor-execution',
      porFinanciador: '/api/v1/reports/by-financier',
      porRegion: '/api/v1/reports/by-region',
      porArea: '/api/v1/reports/by-area',
      partidasDesviacion: '/api/v1/reports/budget-variances',
      conciliacion: '/api/v1/reports/reconciliation',
      auditoriaCambios: '/api/v1/reports/budget-audit-timeline',
      exportarExcel: (tipoReporte: string) => `/api/v1/reports/export?tipo=${tipoReporte}&format=excel`,
      exportarPdf: (tipoReporte: string) => `/api/v1/reports/export?tipo=${tipoReporte}&format=pdf`
    },
    seguridad: {
      usuarios: '/api/v1/users',
      usuarioScopes: (id: number) => `/api/v1/users/${id}/scopes`,
      roles: '/api/v1/roles',
      rolPermisos: (id: number) => `/api/v1/roles/${id}/permissions`,
      permisos: '/api/v1/permissions',
      permisosCatalogo: '/api/v1/roles/permissions/catalog',
      auditoria: '/api/v1/audit',
      verificarIntegridad: '/api/v1/audit/integrity'
    },
    dashboard: {
      kpis: '/api/v1/dashboard/kpis',
      chartsFinanciador: '/api/v1/dashboard/charts/by-financier',
      chartsRegiones: '/api/v1/dashboard/charts/by-region'
    },
    catalogos: {
      gestiones: '/api/v1/catalogs/gestiones',
      regiones: '/api/v1/catalogs/regiones',
      financiadores: '/api/v1/catalogs/financiadores',
      cuentas: '/api/v1/catalogs/cuentas',
      tiposCambio: '/api/v1/catalogs/tipos-cambio'
    }
  }
};
