# Proposal: Modular Budget & Dynamic RBAC Platform for Enseña por Bolivia

## Why

Enseña por Bolivia requiere un Sistema Web de Control Presupuestario y Ejecución Financiera que reemplace el manejo manual de hojas de cálculo con consultas dinámicas sobre sus 7 reportes oficiales. Para organizaciones que administran fondos de cooperación internacional (donantes como CATALYST, CEL, KJCF), es crítico garantizar el principio de mínimo privilegio, control de acceso basado en roles (RBAC) dinámico, restricción de datos territorial y programática (data scoping), y auditoría total de operaciones contables y presupuestarias.

## What Changes

- **Arquitectura Modular Desacoplada**: El sistema se estructura en módulos independientes: Autenticación & Identidad, Presupuestos & Modificaciones, Movimientos Contables (TPS) & Ingesta Excel, Centro de Reportes Oficiales (7 informes), Dashboard Agregador (con mínimo privilegio) y Gobernanza de Seguridad.
- **RBAC Dinámico**: Matriz de permisos atómicos configurables desde el frontend en tiempo real sin requerir cambios de código ni despliegues.
- **Data Scoping Multidimensional**: Restricción automática de acceso a nivel de query según la jurisdicción asignada al usuario (Región: LP/SC, Área: Alumni/Programa, Financiador: fondos específicos).
- **Ingesta y Validación de Excel (TPS)**: Procesamiento masivo por lotes del extracto contable con validación sintáctica/semántica, historial de lotes y capacidad de reversión atómica.
- **Centro de Reportes Financieros**: Motor de consulta y agregación para los 7 informes normativos con filtros combinados y exportación a Excel y PDF con formato institucional.
- **Dashboard Agregador Seguro**: Vista ejecutiva de KPIs y tendencias que consume datos respetando estrictamente el alcance de datos y permisos del usuario logueado.
- **Bitácora de Auditoría (Audit Log)**: Registro inmutable de eventos sensibles (logins, modificaciones presupuestarias, importaciones, cambios de roles/permisos) con captura de estado previo y nuevo en formato JSON.

## Capabilities

### New Capabilities

- `auth-session`: Autenticación institucional, emisión y ciclo de vida de tokens JWT, recuperación de credenciales y forzado de cambio de contraseña en primer inicio.
- `rbac-governance`: Catálogo de permisos atómicos, administración dinámica de roles, data scoping multidimensional (región/área/financiador) y bitácora de auditoría inmutable.
- `budget-management`: Registro de techos presupuestarios anuales por partida/área/financiador y gestión de reformulaciones y traspasos entre partidas con validación de saldos.
- `transaction-movements`: Motor de movimientos contables transaccionales (TPS), ingesta masiva de archivos Excel del sistema contable, validación de integridad y reversión de lotes.
- `financial-reports`: Generación de los 7 reportes financieros normativos, consultas dinámicas multi-criterio y exportación en formatos Excel (.xlsx) y PDF (.pdf).
- `executive-dashboard`: Métricas analíticas consolidadas, semáforos de salud financiera y gráficos de distribución por financiador y tiempo, filtrados bajo mínimo privilegio.

### Modified Capabilities

*(None - initial system capability baseline)*

## Impact

- **Backend**: Implementación en Python / FastAPI con arquitectura modular de routers y servicios, SQLAlchemy / PostgreSQL, y validación estricta de esquemas Pydantic.
- **Frontend**: Aplicación Angular con arquitectura basada en componentes independientes, guards de ruta, directivas de permisos (`*hasPermission`) y servicios modulares para cada dominio.
- **Seguridad**: Autenticación Bearer JWT, inyección de dependencias para validación de permisos en endpoints y filtros de scope automáticos en capas de acceso a datos.
