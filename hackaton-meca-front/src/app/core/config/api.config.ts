/**
 * Configuración de endpoints y URLs de integración con el backend FastAPI
 */
export const API_CONFIG = {
  baseUrl: '/api',
  endpoints: {
    auth: {
      login: '/api/auth/login',
      me: '/api/auth/me',
      refresh: '/api/auth/refresh',
      logout: '/api/auth/logout'
    },
    presupuestos: {
      techos: '/api/presupuestos/techos',
      modificaciones: '/api/presupuestos/modificaciones',
      aprobarModificacion: (id: number) => `/api/presupuestos/modificaciones/${id}/aprobar`,
      resumen: '/api/presupuestos/resumen'
    },
    ejecucion: {
      movimientos: '/api/ejecucion/movimientos',
      subirPlanilla: '/api/ejecucion/importador/subir',
      confirmarLote: (loteId: number) => `/api/ejecucion/importador/${loteId}/confirmar`,
      revertirLote: (loteId: number) => `/api/ejecucion/importador/${loteId}/revertir`,
      lotes: '/api/ejecucion/importador/lotes'
    },
    reportes: {
      ejecucionDonante: '/api/reportes/ejecucion-donante',
      porFinanciador: '/api/reportes/financiador',
      porRegion: '/api/reportes/region',
      porArea: '/api/reportes/area',
      partidasDesviacion: '/api/reportes/desviaciones',
      conciliacion: '/api/reportes/conciliacion',
      auditoriaCambios: '/api/reportes/auditoria-presupuestaria',
      exportarExcel: (tipoReporte: string) => `/api/reportes/exportar?tipo=${tipoReporte}`
    },
    seguridad: {
      usuarios: '/api/seguridad/usuarios',
      roles: '/api/seguridad/roles',
      permisos: '/api/seguridad/permisos',
      auditoria: '/api/seguridad/auditoria',
      verificarIntegridad: '/api/seguridad/auditoria/verificar-integridad'
    }
  }
};
