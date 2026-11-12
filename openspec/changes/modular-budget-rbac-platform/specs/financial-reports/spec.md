# Spec Delta: Financial Reports Suite

## Purpose

Delivers the seven standardized financial execution reports with dynamic filtering, aggregation by fiscal dimensions, and export generation to Excel and PDF formats.

## ADDED Requirements

### Requirement: Seven canonical execution reports generation
The system SHALL compute aggregated budget versus execution summaries across seven standard report types: rubric and account, financier, area and financier, region, monthly progression, movement details, and consolidated summary.

#### Scenario: Querying execution by financier report
- **WHEN** an authorized user requests the execution by financier report for the current fiscal year
- **THEN** the system returns aggregated approved budget, actual execution, remaining balance, and percentage execution grouped by funding source.

### Requirement: Report export to spreadsheet and document formats
The system SHALL export the results of any of the seven reports into formatted Microsoft Excel (.xlsx) workbooks and formal executive PDF documents with institutional branding.

#### Scenario: Exporting report to Excel format
- **WHEN** an authorized user triggers an Excel export for an active report view
- **THEN** the system generates and streams a binary spreadsheet file containing formatted data tables and applied filter headers.

#### Scenario: Exporting report to PDF format
- **WHEN** an authorized user triggers a PDF export for an active report view
- **THEN** the system renders and streams an executive PDF document including institutional headers, signature blocks, and summary tables.
