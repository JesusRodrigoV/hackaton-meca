import hashlib

import pytest
from jose import JWTError

from app.core.enums import TokenType
from app.core.security import (
    create_2fa_session_token,
    create_access_token,
    create_change_password_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_token,
    verify_password,
)


def test_hash_token_is_sha256_and_deterministic():
    raw = "token-de-prueba"
    expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    assert hash_token(raw) == expected
    assert hash_token(raw) == hash_token(raw)
    assert hash_token(raw) != hash_token(f"{raw}-otro")


def test_password_hash_roundtrip_and_long_password():
    password = "ContraseñaSegura123!"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True
    assert verify_password("otra-clave", hashed) is False
    assert verify_password("x" * 100, get_password_hash("x" * 100)) is True


def test_access_token_has_expected_claims():
    token = create_access_token(42)
    payload = decode_token(token, TokenType.ACCESS)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_refresh_token_has_jti_and_expiry():
    refresh = create_refresh_token(42, device_info="pytest")
    payload = decode_token(refresh["token"], TokenType.REFRESH)

    assert refresh["jti"] == payload["jti"]
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"
    assert refresh["expires_at"] is not None


def test_token_type_mismatch_is_rejected():
    access = create_access_token(42)

    with pytest.raises(JWTError):
        decode_token(access, TokenType.REFRESH)


def test_qr_code_generation_returns_valid_png_data_uri():
    from app.crud.two_factor import generate_qr_code_data_uri
    uri = "otpauth://totp/Enseña%20por%20Bolivia:test@test.com?secret=JBSWY3DPEHPK3PXP"
    qr_data = generate_qr_code_data_uri(uri)
    assert qr_data.startswith("data:image/png;base64,")
    assert len(qr_data) > 100


def test_change_password_and_two_factor_token_types():
    change_payload = decode_token(
        create_change_password_token(7),
        TokenType.CHANGE_PASSWORD,
    )
    two_factor_payload = decode_token(
        create_2fa_session_token(7),
        TokenType.PRE_2FA,
    )

    assert change_payload["type"] == "change_password"
    assert two_factor_payload["type"] == "pre_2fa"
    assert change_payload["sub"] == "7"
    assert two_factor_payload["sub"] == "7"