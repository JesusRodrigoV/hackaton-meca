from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core.policia import is_account_locked, remaining_lockout_minutes
from app.core.security import get_password_hash
from app.crud import auth as crud_auth
from app.services.auth import validate_two_factor_code


def test_authenticate_credentials_success(monkeypatch):
    user = SimpleNamespace(password_hash=get_password_hash("ClaveSegura123!"))
    monkeypatch.setattr(
        crud_auth,
        "get_user_by_email",
        lambda db, email: user,
    )

    assert crud_auth.authenticate_credentials(None, "user@example.com", "ClaveSegura123!") is user


def test_authenticate_credentials_rejects_wrong_password(monkeypatch):
    user = SimpleNamespace(password_hash=get_password_hash("ClaveSegura123!"))
    monkeypatch.setattr(
        crud_auth,
        "get_user_by_email",
        lambda db, email: user,
    )

    assert crud_auth.authenticate_credentials(None, "user@example.com", "incorrecta") is None


def test_authenticate_credentials_rejects_missing_user(monkeypatch):
    monkeypatch.setattr(
        crud_auth,
        "get_user_by_email",
        lambda db, email: None,
    )

    assert crud_auth.authenticate_credentials(None, "nadie@example.com", "x") is None


def test_account_lockout_state_uses_locked_until():
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    past = datetime.now(timezone.utc) - timedelta(seconds=1)

    assert is_account_locked(SimpleNamespace(locked_until=future)) is True
    assert is_account_locked(SimpleNamespace(locked_until=past)) is False
    assert is_account_locked(SimpleNamespace(locked_until=None)) is False
    assert remaining_lockout_minutes(SimpleNamespace(locked_until=future)) >= 1


def test_two_factor_validation_accepts_totp_and_rejects_backup_on_disable(monkeypatch):
    user = SimpleNamespace(id=1, totp_secret="encrypted-secret")
    monkeypatch.setattr(
        "app.services.auth.crud_2fa.get_user_totp_secret",
        lambda current_user: "BASE32SECRET",
    )
    monkeypatch.setattr(
        "app.services.auth.crud_2fa.verify_totp_code",
        lambda secret, code: code == "123456",
    )

    assert (
        validate_two_factor_code(object(), user, "123456", allow_backup=False)
        is True
    )
    assert (
        validate_two_factor_code(object(), user, "000000", allow_backup=False)
        is False
    )