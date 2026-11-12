from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.crud.user import get_user_by_email
from app.models.security import User


def authenticate_credentials(
    db: Session,
    email: str,
    password: str,
) -> Optional[User]:
    """Return the user when email + password match.

    Account state (active, lockout, 2FA, forced password change) is evaluated by
    the auth service/endpoint, not here.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user