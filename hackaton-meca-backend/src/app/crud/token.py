from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.models.refresh_token import RefreshToken
#reset token
from app.models.password_reset_token import PasswordResetToken
from app.core.config import settings
from app.models.user import User
import secrets

def create_refresh_token_record(
    db: Session,
    user_id: str,
    jti: str,
    expires_at: datetime,
    device_info: Optional[str] = None
) -> RefreshToken:
    token = RefreshToken(
        user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        device_info=device_info,
        revoked=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token

def revoke_refresh_token_by_jti(db: Session, jti: str) -> Optional[RefreshToken]:
    token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not token:
        return None
    if not token.revoked:
        token.revoked = True
        db.add(token)
        db.commit()
        db.refresh(token)
    return token

def is_refresh_token_valid(db: Session, jti: str) -> bool:
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.jti == jti, RefreshToken.revoked == False)
        .first()
    )
    if not token:
        return False
    return token.expires_at > datetime.now(timezone.utc)

#funciones reset token
def create_password_reset_token(db: Session, user_id: str) -> str:
    """
    Crea, guarda y devuelve un nuevo token de reseteo de contraseña
    """
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user_id).delete()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    
    db_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    
    return token

def get_user_by_reset_token(db: Session, token: str) -> User | None:
    db_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first() 
    if not db_token:
        return None 
        
    if db_token.expires_at < datetime.now(timezone.utc):
        db.delete(db_token) 
        db.commit()
        return None 
        
    return db.query(User).get(db_token.user_id)

def delete_reset_token(db: Session, token: str) -> None:
    db.query(PasswordResetToken).filter(PasswordResetToken.token == token).delete()
    db.commit()
