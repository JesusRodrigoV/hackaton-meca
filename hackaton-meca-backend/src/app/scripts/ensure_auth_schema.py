"""Bring the legacy Docker SQL schema up to date for the current auth models."""

from sqlalchemy import text

from app.db.session import engine
from app.models.auth import PasswordResetToken, RefreshToken, TwoFactorBackupCode
from app.models.audit import AuditChainHead


def ensure_auth_schema() -> None:
    """Apply additive, repeatable compatibility DDL without dropping data."""
    user_columns = (
        "totp_secret TEXT",
        "is_totp_enabled BOOLEAN NOT NULL DEFAULT FALSE",
        "totp_enabled_at TIMESTAMPTZ",
        "must_change_password BOOLEAN NOT NULL DEFAULT FALSE",
        "password_changed_at TIMESTAMPTZ",
    )
    with engine.begin() as connection:
        for definition in user_columns:
            column_name = definition.split()[0]
            connection.execute(
                text(
                    f"ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                    f"{column_name} {definition[len(column_name):].strip()}"
                )
            )

        connection.execute(
            text("ALTER TABLE permissions ADD COLUMN IF NOT EXISTS name VARCHAR(120)")
        )
        connection.execute(text("UPDATE permissions SET name = code WHERE name IS NULL"))
        connection.execute(text("ALTER TABLE permissions ALTER COLUMN name SET NOT NULL"))
        connection.execute(
            text(
                "ALTER TABLE permissions ADD COLUMN IF NOT EXISTS "
                "is_active BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )

        for model in (RefreshToken, PasswordResetToken, TwoFactorBackupCode, AuditChainHead):
            model.__table__.create(bind=connection, checkfirst=True)

        connection.execute(
            text(
                "INSERT INTO audit_chain_head (id, last_hash) VALUES (1, NULL) "
                "ON CONFLICT (id) DO NOTHING"
            )
        )


if __name__ == "__main__":
    ensure_auth_schema()
