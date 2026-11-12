from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.security import get_password_hash
from app.services import auth as auth_service
from app.services import rbac as rbac_service
from app.services import users as user_service


def test_change_password_rejects_weak_password():
    user = SimpleNamespace(
        id=1,
        password_hash=get_password_hash("ClaveSegura123!"),
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_service.change_password(None, user, "ClaveSegura123!", "123")

    assert exc_info.value.status_code == 400
    assert "12 caracteres" in exc_info.value.detail


def test_update_user_rejects_self_deactivation():
    user = SimpleNamespace(id=5)

    with pytest.raises(HTTPException) as exc_info:
        user_service.update_user(
            None,
            user,
            current_user_id=5,
            is_active=False,
        )

    assert exc_info.value.status_code == 400
    assert "propia cuenta" in exc_info.value.detail


def test_create_permission_rejects_duplicate_code(monkeypatch):
    monkeypatch.setattr(
        "app.services.rbac.crud_permission.get_permission_by_code",
        lambda db, code: SimpleNamespace(id=1),
    )

    with pytest.raises(HTTPException) as exc_info:
        rbac_service.create_permission(
            None,
            code="usuarios.admin",
            name="Administrar usuarios",
            module="usuarios",
        )

    assert exc_info.value.status_code == 409


def test_deactivate_permission_sets_inactive(monkeypatch):
    permission = SimpleNamespace(id=1, is_active=True)
    monkeypatch.setattr(
        "app.services.rbac.crud_permission.get_permission",
        lambda db, permission_id: permission,
    )

    def fake_update(db, current_permission, *, is_active):
        current_permission.is_active = is_active
        return current_permission

    monkeypatch.setattr(
        "app.services.rbac.crud_permission.update_permission",
        fake_update,
    )

    result = rbac_service.deactivate_permission(None, 1)

    assert result.is_active is False