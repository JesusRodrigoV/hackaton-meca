# Product: Sistema de Control Presupuestario y Ejecución Financiera

## Platform
- **Type**: Web Application
- **Frontend**: Angular 22 (Standalone components, TypeScript, SCSS)
- **Backend**: Python / FastAPI
- **Database**: PostgreSQL

## Purpose
Sistema institucional para **Enseña por Bolivia** que centraliza y automatiza el control presupuestario, la ingesta masiva de movimientos contables y la rendición de cuentas a fondos de cooperación internacional (donantes como CATALYST, CEL, KJCF) mediante 7 reportes oficiales y un dashboard analítico con estricto principio de mínimo privilegio.

## Primary Users & Roles
1. **Director General / Super Admin**: Control institucional total, administración de roles, usuarios y visualización nacional consolidada.
2. **Técnico / Responsable de Finanzas**: Carga y reversión de lotes contables en Excel, formulación de presupuestos y generación de reportes normativos.
3. **Coordinadores de Área / Proyecto** (ej. Alumni, Formación, La Paz, Santa Cruz): Consulta de presupuestos y ejecución restringida a su jurisdicción territorial y programática.
4. **Auditores Externos / Donantes**: Acceso de solo lectura restringido exclusivamente a los fondos y proyectos financiados por su entidad.

## Key Capabilities
- **Autenticación & Identidad**: Tokens JWT, expiración de sesiones y forzado de cambio de contraseña en primer inicio.
- **RBAC Dinámico & Data Scoping**: Asignación granular de permisos operacionales y restricciones de visualización automática por Región, Área y Financiador.
- **Presupuestos**: Techos presupuestarios anuales y reformulaciones con validación de saldo disponible.
- **Movimientos (TPS)**: Ingesta masiva y validación de hojas Excel del sistema contable con capacidad de reversión atómica por lote.
- **Los 7 Reportes Oficiales**:
  1. Ejecución por rubro y cuenta
  2. Ejecución por financiador
  3. Ejecución por área y financiador
  4. Ejecución por región
  5. Ejecución por mes
  6. Detalle de movimientos
  7. Resumen general consolidado
- **Dashboard Ejecutivo**: Sala de control analítica con KPIs y distribución de gasto respetando el scope del usuario.
- **Bitácora de Auditoría**: Trazabilidad inmutable de cambios y operaciones sensibles con snapshots JSON de estado previo y nuevo.
