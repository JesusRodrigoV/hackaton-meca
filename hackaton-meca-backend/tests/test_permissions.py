from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.dependencies import require_permission
from app.core.enums import PermissionCode
from app.crud.permission import has_all_permissions


def test_has_all_permissions_requires_every_code():
    effective = {"dashboard.ver", "auditoria.ver"}

    assert has_all_permissions(effective, ["dashboard.ver"]) is True
    assert has_all_permissions(effective, ["dashboard.ver", "auditoria.ver"]) is True
    assert has_all_permissions(effective, ["usuarios.admin"]) is False
    assert has_all_permissions(effective, []) is True


def test_require_permission_allows_user_with_permission(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.crud_permission.user_has_permissions",
        lambda db, user_id, required: True,
    )
    dependency = require_permission(PermissionCode.USUARIOS_ADMIN)
    user = SimpleNamespace(id=1, is_active=True)

    assert dependency(current_user=user, db=object()) is user


def test_require_permission_denies_user_without_permission(monkeypatch):
    monkeypatch.setattr(
        "app.core.dependencies.crud_permission.user_has_permissions",
        lambda db, user_id, required: False,
    )
    dependency = require_permission(PermissionCode.USUARIOS_ADMIN)
    user = SimpleNamespace(id=1, is_active=True)

    with pytest.raises(HTTPException) as exc_info:
        dependency(current_user=user, db=object())

    assert exc_info.value.status_code == 403
    assert "Permisos insuficientes" in exc_info.value.detail


def test_require_permission_without_requirements_returns_user():
    dependency = require_permission()
    user = SimpleNamespace(id=1, is_active=True)

    assert dependency(current_user=user, db=object()) is user