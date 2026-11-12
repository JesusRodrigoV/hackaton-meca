# Spec Delta: Budget Management

## Purpose

Enables creation and tracking of annual budget ceilings, item formulation, and transparent budget reformulations with balance validation.

## ADDED Requirements

### Requirement: Budget ceiling formulation
The system SHALL store and manage approved annual budget ceilings segmented by fiscal year, program area, account rubric, and funding partner.

#### Scenario: Registering annual budget allocation
- **WHEN** an authorized finance officer creates an annual budget line with year, rubric, area, and financier
- **THEN** the system persists the approved amount and marks it available for execution tracking.

### Requirement: Budget reformulation and transfer validation
The system SHALL validate and record budget transfers between rubrics or areas, preventing transfers that exceed the available source balance.

#### Scenario: Valid transfer between budget lines
- **WHEN** an authorized user requests a transfer where the source line has sufficient uncommitted budget
- **THEN** the system debits the source line, credits the target line, records the justification, and logs the modification.

#### Scenario: Rejection of transfer exceeding available balance
- **WHEN** a transfer request amount exceeds the available budget on the source line
- **THEN** the system rejects the operation with an HTTP 422 Unprocessable Entity error indicating insufficient funds.
