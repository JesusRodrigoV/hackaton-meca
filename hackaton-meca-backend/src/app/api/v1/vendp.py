from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.core.security import verify_password
from app.core.encryption import decrypt_data
from app.core.rsa_manager import RSAManager
from app.core import sms_service
from app.core.password_policy import validate_password_strength_func
from app.crud import user as crud_user
from app.crud import two_factor as crud_2fa
from app.schemas.two_factor import (
    TOTPSetupResponse, TOTPVerifyRequest, 
    TOTPBackupCodesResponse, TOTPDisableRequest
)

router = APIRouter()


class ChangePasswordRequestCodeResponse(BaseModel):
    message: str
    masked_phone: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=1)
    code: str = Field(..., min_length=6, max_length=10)


def _mask_phone(phone_number: str | None) -> str:
    if not phone_number:
        return "tu numero registrado"
    visible = phone_number[-3:]
    hidden_count = max(len(phone_number) - 3, 0)
    return f"{'*' * hidden_count}{visible}"


def _decrypt_password_or_400(encrypted_password: str) -> str:
    try:
        return RSAManager.decrypt_password(encrypted_password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de seguridad: la contrasena debe estar cifrada correctamente.",
        )


@router.post(
    "/change-password/request-code",
    response_model=ChangePasswordRequestCodeResponse,
    summary="Solicitar codigo SMS para cambiar contrasena",
)
async def request_change_password_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu cuenta no tiene un numero de celular registrado.",
        )

    code = crud_user.create_sms_otp(db, current_user, "change_password")
    try:
        await sms_service.send_otp(current_user.phone_number, code, "change_password")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el codigo SMS. Intenta nuevamente.",
        )

    return {
        "message": "Codigo enviado exitosamente.",
        "masked_phone": _mask_phone(current_user.phone_number),
    }


@router.post("/change-password/verify-and-change", summary="Verificar SMS y cambiar contrasena")
def verify_and_change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    current_password = _decrypt_password_or_400(body.current_password)
    new_password = _decrypt_password_or_400(body.new_password)

    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La contrasena actual no es correcta.",
        )

    try:
        validate_password_strength_func(new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if verify_password(new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contrasena debe ser diferente a la actual.",
        )

    if crud_user.is_password_in_history(db, current_user, new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes reutilizar una contrasena que ya has usado anteriormente.",
        )

    if not crud_user.verify_sms_otp(db, current_user, body.code, "change_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo SMS invalido o expirado.",
        )

    crud_user.update_password(db, db_user=current_user, new_password=new_password)
    return {"message": "Contrasena actualizada exitosamente."}

@router.post("/2fa/enable", response_model=TOTPSetupResponse, summary="Iniciar activacion de 2FA")
def setup_2fa(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA esta activo:)")
    
    #secreto
    secret = crud_2fa.generate_totp_secret()
    crud_2fa.save_totp_secret_for_user(db, user=current_user, secret=secret)
    
    #uri
    otpauth_uri = crud_2fa.get_otpauth_uri(secret, current_user.email)
    
    return {"secret": secret, "otpauth_uri": otpauth_uri}

@router.post("/2fa/verify", response_model=TOTPBackupCodesResponse, summary="Verificar y activar 2FA :)")
def verify_2fa(
    body: TOTPVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.is_totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA esta activo:)")
    if not current_user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes iniciar el proceso /2fa/enable primero")

    try:
        secret = decrypt_data(current_user.totp_secret)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al descifrar el secreto")
    
    if not crud_2fa.verify_totp_code(secret, body.totp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Codigo invalido. TRY AGAIN")

    crud_2fa.activate_totp_for_user(db, user=current_user)
    
    plaintext_codes = crud_2fa.generate_and_store_backup_codes(db, user=current_user)
    
    return {"backup_codes": plaintext_codes}

@router.post("/2fa/disable", status_code=status.HTTP_204_NO_CONTENT, summary="Desactivar 2FA")
def disable_2fa(
    body: TOTPDisableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):

    if not current_user.is_totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA YA NO ESTA ACTIVO:(")
    
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Contraseña incorrecta")
        
    crud_2fa.disable_totp_for_user(db, user=current_user)
    
    return None
