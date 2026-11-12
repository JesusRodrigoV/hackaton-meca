# Tasks

## 1. Database Schema & Seed Setup

- [ ] 1.1 Define PostgreSQL schema models in backend for `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `user_scopes`, `audit_logs`, `budgets`, `movements`, `financiers`, `regions`, and `areas`, verifying migration runs cleanly
- [ ] 1.2 Implement database seed script inserting the atomic permissions catalogue and default roles (Super Admin, Finanzas, Coordinador de Área, Auditor Donante), verifying seeded records exist in database

## 2. Authentication & Authorization Middleware

- [ ] 2.1 Implement `/auth/login`, `/auth/refresh`, and `/auth/change-password` endpoints with bcrypt hashing and JWT tokens, verifying token generation and forced password change workflow with automated tests
- [ ] 2.2 Implement `require_permission` decorator for FastAPI dependency injection, verifying 403 Forbidden responses on unauthorized requests
- [ ] 2.3 Implement `apply_user_scopes` database query interceptor filtering by region, area, and financier, verifying unit tests restrict returned rows per scope

## 3. Transactional Movements (TPS) & Excel Ingestion

- [ ] 3.1 Implement Excel parser and validation service with Pandas/OpenPyXL, verifying validation against schema and dimension FKs
- [ ] 3.2 Implement `POST /movements/import-excel` with batch ID assignment and atomic transaction commit, verifying imported rows in movements table
- [ ] 3.3 Implement `DELETE /movements/batches/{batch_id}` for batch rollback and `GET /movements` with server-side pagination, verifying rollback removes records cleanly

## 4. Budget Ceilings & Modifications Engine

- [ ] 4.1 Implement `GET /budgets` and `POST /budgets` for annual ceiling formulation, verifying permissions and scoped access
- [ ] 4.2 Implement `POST /budgets/modifications` verifying validation prevents transfers exceeding source uncommitted balance and logs audit trail

## 5. 7 Canonical Financial Reports Suite

- [ ] 5.1 Implement report aggregation endpoints for reports 1 through 7 (rubric/account, financier, area/financier, region, monthly, movement details, consolidated summary), verifying mathematical accuracy against spreadsheet source
- [ ] 5.2 Implement streaming report export to Excel (.xlsx) and PDF (.pdf) with institutional header formatting, verifying binary downloads

## 6. Scoped Executive Dashboard Backend

- [ ] 6.1 Implement `GET /dashboard/kpis` returning total budget, executed amount, balance, and execution percentage under strict `apply_user_scopes`
- [ ] 6.2 Implement `GET /dashboard/charts/by-financier` and `GET /dashboard/charts/monthly-trend`, verifying visual data series format

## 7. Security & Governance Administration Endpoints

- [ ] 7.1 Implement CRUD endpoints for users with `user_scopes` assignment and password reset, verifying audit logs capture state changes
- [ ] 7.2 Implement role and permission matrix management endpoints, verifying dynamic permission toggling takes immediate effect
- [ ] 7.3 Implement `GET /admin/audit-logs` endpoint with filters by user, action, and date range

## 8. Frontend Master Suites (Angular)

- [ ] 8.1 Build Login and forced password change screens with reactive forms and auth store in Angular
- [ ] 8.2 Build main layout shell with collapsible Sidebar, Topbar showing active scope badge, and `*hasPermission` structural directive
- [ ] 8.3 Build Executive Dashboard suite with KPI summary cards and Chart.js/ApexCharts visualizations
- [ ] 8.4 Build Budget Ceilings and Modifications screens with data tables and transfer modals
- [ ] 8.5 Build Movements Ledger and Excel Drag-and-Drop Ingestion suite with upload feedback and batch rollback buttons
- [ ] 8.6 Build Financial Reports Center suite featuring 7-in-1 tabbed views, combined multi-filters, and Excel/PDF export buttons
- [ ] 8.7 Build Security & Governance suite with Users directory, Dynamic RBAC checkbox matrix, and Audit Log timeline

## 9. End-to-End Verification & Role Simulation

- [ ] 9.1 Run simulated end-to-end user journeys verifying Super Admin, Finance Officer, Santa Cruz Coordinator, and External Donante profiles receive strictly scoped views and permissions
