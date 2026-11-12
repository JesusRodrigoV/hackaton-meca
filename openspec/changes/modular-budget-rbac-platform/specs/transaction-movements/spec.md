# Spec Delta: Transaction Movements & Excel Ingestion

## Purpose

Handles high-throughput financial journal entries, bulk Excel upload from accounting software, validation of transaction integrity, and batch rollback capabilities.

## ADDED Requirements

### Requirement: Batch Excel ingestion and data validation
The system SHALL accept accounting ledger Excel files, validating schema structure, account codes, and numeric consistency prior to persistence.

#### Scenario: Successful Excel spreadsheet processing
- **WHEN** an authorized user uploads a conforming Excel ledger file
- **THEN** the system parses rows, checks dimension foreign keys, saves records under a new batch ID, and returns a summary of ingested rows.

#### Scenario: Ingestion rejection on malformed data
- **WHEN** an uploaded file contains missing mandatory headers or corrupt data formats
- **THEN** the system rejects the entire batch, rolls back changes, and returns detailed line-by-line error messages.

### Requirement: Transaction ledger querying with pagination
The system SHALL provide paginated and filterable querying across accounting movements, applying user data scoping restrictions automatically.

#### Scenario: Filtered movement inquiry
- **WHEN** a user queries movements specifying date ranges and account rubrics within their permitted scope
- **THEN** the system returns matching records with pagination metadata and total matching counts.

### Requirement: Atomic batch rollback
The system SHALL allow authorized administrators to revert an entire imported batch of movements in an atomic operation.

#### Scenario: Rolling back an erroneous import batch
- **WHEN** an authorized finance officer triggers a rollback for an existing batch ID
- **THEN** the system deletes all associated movements atomically, updates budget execution counters, and logs the deletion.
