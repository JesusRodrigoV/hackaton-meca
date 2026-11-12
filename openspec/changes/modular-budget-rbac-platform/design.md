# Design: Modular Financial Platform with Dynamic RBAC & Least-Privilege Scoping

## Context

See `proposal.md` for motivation and domain problem statement. The project requires a web application for Enseña por Bolivia replacing static Excel spreadsheets with a centralized, modular financial system. The frontend is built with Angular in `hackaton-meca-front` and the backend is Python / FastAPI backed by PostgreSQL.

## Goals / Non-Goals

**Goals:**
- Provide a decoupled modular architecture where each domain (Auth, Presupuestos, Movimientos TPS, Reportes, Dashboard, Seguridad) has dedicated frontend screens and backend services.
- Implement strict least-privilege data scoping (`apply_user_scopes`) intercepting all queries for region, area, and financier restrictions.
- Deliver real-time dynamic RBAC allowing administrators to toggle permissions without code redeployments.
- Expose the 7 required financial reports with multi-criteria dynamic filtering, live aggregation, and streaming exports to Excel and PDF.
- Record structured audit logs with previous and current JSON snapshots for critical financial and administrative operations.

**Non-Goals:**
- Direct two-way sync or live ODBC connection to the legacy accounting desktop software (Excel ledger upload is the designated ingestion boundary).
- Complex multi-currency live Forex trading calculations (only dual currency Bs / USD with configurable exchange rates is supported).

## Decisions

### 1. Architectural Decoupling: Dashboard as Read-Only Consumer
- **Decision**: The Dashboard is treated as a downstream read-only consumer module rather than an entry point or monolithic core.
- **Rationale**: Prevents coupling domain logic into a central view. Allows users without dashboard permissions to access operational modules directly, and guarantees that KPI aggregations strictly enforce user scopes.
- **Alternatives considered**: Monolithic dashboard controller computing all stats in one query. Rejected due to poor separation of concerns and high risk of privilege leakage.

### 2. Dual-Layer Authorization: Atomic Permissions + Dimensional Scoping
- **Decision**: Authorize in two orthogonal layers:
  1. *Layer A (Operational RBAC)*: `require_permission("module:action")` validating whether the user can invoke the operation.
  2. *Layer B (Data Scoping)*: `apply_user_scopes(query, user, model)` filtering database rows based on assigned regions, areas, and financiers.
- **Rationale**: An area coordinator may have permission `reports:view`, but should only see data for their assigned area or region. Decoupling permissions from data boundaries enables clean, reusable code.
- **Alternatives considered**: Hardcoding roles into business logic (e.g. `if user.role == 'AREA_COORDINATOR'`). Rejected because it breaks dynamic role creation and makes organizational restructuring impossible without code changes.

### 3. Screen Structure: 8 Master Suites in Frontend
- **Decision**: Group frontend views into 8 cohesive master screens rather than 16 fragmented routes:
  1. Login & Password Rotation
  2. Executive Dashboard (KPIs, Charts, Semaphores)
  3. Budget Ceilings formulation
  4. Budget Modifications & Transfers
  5. Accounting Movements Ledger (TPS view)
  6. Bulk Excel Ingestion & Batch Rollback
  7. Financial Reports Center (7-in-1 interactive suite with Excel/PDF export)
  8. Security & Governance Center (Users, Roles/Permissions matrix, Audit Log)
- **Rationale**: Significantly improves user experience and developer velocity in a hackathon while maintaining complete functional coverage.

### 4. Excel Ingestion Engine (TPS Processing)
- **Decision**: Ingest spreadsheets via FastAPI streaming upload, validate headers and data types with Pandas/OpenPyXL in memory, and persist rows in a single database transaction assigned to a `batch_id`.
- **Rationale**: Allows atomic rollback of an entire batch if errors are detected post-import.

## Data Model Architecture

```
   +--------------------+       +--------------------+       +--------------------+
   |       users        |----<  |     user_roles     |  >----|       roles        |
   +--------------------+       +--------------------+       +--------------------+
             |                                                         |
             |                                                         |
             | scopes (region, area, financier)                        v
             v                                               +--------------------+
   +--------------------+                                    |  role_permissions  |
   |    user_scopes     |                                    +--------------------+
   +--------------------+                                              |
                                                                       v
   +--------------------+                                    +--------------------+
   |     audit_logs     |                                    |    permissions     |
   +--------------------+                                    +--------------------+

   +------------------------------------------------------------------------------+
   |                            FINANCIAL DOMAIN                                  |
   |                                                                              |
   |   [financiers] <---+           [regions] <---+           [areas] <---+       |
   |                    |                         |                       |       |
   |                    +-------------+-----------+-----------+           |       |
   |                                  |                       |           |       |
   |                                  v                       v           |       |
   |                           [budgets]                 [movements] <----+       |
   |                           (ceilings, year,          (ledger rows,            |
   |                            rubric, amount)           batch_id, glosa)        |
   +------------------------------------------------------------------------------+
```

## Risks / Trade-offs

- **[Performance on Aggregated Reports]** Large movement volumes could slow down on-the-fly report calculation.
  → *Mitigation*: Index composite keys `(fiscal_year, financier_id, region_id, area_id)` and use SQL aggregation functions (`SUM`, `GROUP BY`) rather than in-memory Python loops.
- **[Audit Log Growth]** High-volume JSON snapshot auditing could rapidly inflate storage.
  → *Mitigation*: Audit only state-changing operations (CREATE, UPDATE, DELETE, IMPORT, LOGIN) and exclude read-only GET queries from full payload capture.
- **[Permission Synchronization in Frontend]** User permission changes in the database might become stale in the browser.
  → *Mitigation*: Embed permission hashes in the short-lived JWT access token and refresh state on token refresh or re-login.
