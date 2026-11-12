# Spec Delta: Auth & Session

## Purpose

Provides secure user authentication, session lifecycle with JWT tokens, password security policies, and forced initial password rotation for Enseña por Bolivia.

## ADDED Requirements

### Requirement: User authentication with credentials
The system SHALL validate username or email and password, issuing an authentication token pair (access and refresh token) upon successful verification.

#### Scenario: Successful login with valid credentials
- **WHEN** an active user submits valid email and password credentials
- **THEN** the system returns an HTTP 200 response with access token, refresh token, user profile data, and assigned roles.

#### Scenario: Rejected login with inactive account
- **WHEN** a user marked as inactive attempts to authenticate
- **THEN** the system rejects the request with an HTTP 403 Forbidden error indicating the account is deactivated.

### Requirement: Forced password rotation on initial access
The system SHALL enforce mandatory password reset when a user account has the temporary password flag active, preventing access to operational endpoints until updated.

#### Scenario: Mandatory password change prompt
- **WHEN** a user with the force password change flag logs in
- **THEN** the system restricts operational API calls and returns a requirement to submit a new password meeting security criteria.

#### Scenario: Completion of password rotation
- **WHEN** the user provides a compliant new password on the change password endpoint
- **THEN** the system updates the password hash, clears the forced change flag, and grants full operational access.
