# Spec Delta: Executive Dashboard

## Purpose

Aggregates high-level financial indicators, health indicators, and execution charts while enforcing strict least privilege and user jurisdiction filtering.

## ADDED Requirements

### Requirement: Scoped KPI metric cards computation
The system SHALL aggregate approved budget, total executed spend, uncommitted balance, and global percentage execution strictly within the authenticated user's authorized data scope.

#### Scenario: Displaying KPIs for restricted regional coordinator
- **WHEN** a coordinator assigned solely to Santa Cruz loads dashboard metrics
- **THEN** the KPI summary cards aggregate and reflect only figures related to Santa Cruz operations.

#### Scenario: Displaying KPIs for unrestricted executive
- **WHEN** an executive director with unrestricted scope loads dashboard metrics
- **THEN** the KPI summary cards calculate the consolidated national totals.

### Requirement: Interactive trend and distribution charts
The system SHALL provide analytical chart endpoints delivering execution breakdowns by financier and historical monthly expenditure curves adhering to least privilege.

#### Scenario: Financier breakdown chart rendering
- **WHEN** an authorized user requests chart distribution data
- **THEN** the system returns dataset series grouped by allowed funding sources for visual rendering.
