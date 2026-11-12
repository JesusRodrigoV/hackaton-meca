# Spec Delta: RBAC Governance & Data Scoping

## Purpose

Enforces dynamic role-based access control, atomic system permissions, multi-dimensional data scoping (region, area, financier), and comprehensive audit logging.

## ADDED Requirements

### Requirement: Dynamic role and permission management
The system SHALL provide an administrative interface and endpoints to create, modify, and assign permissions to custom roles in real time.

#### Scenario: Updating role permissions dynamically
- **WHEN** an administrator modifies the set of permissions assigned to a role
- **THEN** all subsequent authorization checks for users with that role immediately reflect the updated permissions without service restart.

### Requirement: Multi-dimensional data scoping enforcement
The system SHALL intercept queries and automatically scope accessible financial data according to the user's assigned regions, areas, and financiers.

#### Scenario: Query restriction by regional jurisdiction
- **WHEN** a user scoped only to region Santa Cruz requests movements or budget figures
- **THEN** the backend automatically injects filter constraints restricting returned data to Santa Cruz.

#### Scenario: Unrestricted access for super administrator
- **WHEN** a user with global administrative privilege queries movements or budgets
- **THEN** the backend executes the query without jurisdiction constraints, returning all organizational data.

### Requirement: Immutable audit logging of sensitive operations
The system SHALL record an audit event for every sensitive action including user management, role adjustments, budget modifications, and bulk data imports.

#### Scenario: Audit log generation on budget modification
- **WHEN** an authorized user updates or reformulates a budget item
- **THEN** the system creates an immutable audit record capturing timestamp, user identifier, action code, target entity, and previous vs new states in JSON.
