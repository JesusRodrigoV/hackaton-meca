import secrets
from typing import List

import pyotp
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_data, encrypt_data
from app.core.security import get_password_hash, verify_password
from app.models.two_factor_codes import TwoFactorCodes
from app.models.user import User


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_otpauth_uri(secret: str, email: str, issuer_name: str = "ZooConnect") -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer_name)


def save_totp_secret_for_user(db: Session, user: User, secret: str):
    user.totp_secret = encrypt_data(secret)
    user.is_totp_enabled = False
    db.add(user)
    db.commit()


def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def activate_totp_for_user(db: Session, user: User):
    user.is_totp_enabled = True
    db.add(user)
    db.commit()


def disable_totp_for_user(db: Session, user: User):
    user.totp_secret = None
    user.is_totp_enabled = False
    db.add(user)
    db.query(TwoFactorCodes).filter(TwoFactorCodes.user_id == user.id).delete()

    db.commit()


def generate_and_store_backup_codes(db: Session, user: User) -> List[str]:
    db.query(TwoFactorCodes).filter(TwoFactorCodes.user_id == user.id).delete()

    plaintext_codes = []
    codes_to_add_to_db = []

    for _ in range(5):
        code = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}"
        plaintext_codes.append(code)

        hashed_code = get_password_hash(code)

        db_code = TwoFactorCodes(user_id=user.id, code_hash=hashed_code)
        codes_to_add_to_db.append(db_code)

    db.add_all(codes_to_add_to_db)
    db.commit()

    return plaintext_codes


def validate_backup_code(db: Session, user: User, code: str) -> bool:
    all_codes = (
        db.query(TwoFactorCodes)
        .filter(TwoFactorCodes.user_id == user.id, TwoFactorCodes.is_used == False)
        .all()
    )

    for db_code in all_codes:
        if verify_password(code, db_code.code_hash):
            db_code.is_used = True
            db.add(db_code)
            db.commit()
            return True
    return False