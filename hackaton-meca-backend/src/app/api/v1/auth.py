from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
    Response,
    Cookie,
)
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import logging

from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserOut,
    UserUpdateProfile,
    UserProfileOut,
    UserCreateResponse,
)
from app.crud import user as crud_user
from app.crud import token as crud_token
from app.crud.auth import authenticate_user
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.models.user import User

# reset token and email verification
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    EmailVerificationRequest,
    ResendVerificationRequest,
    UpdatePhoneRequest,
)

from app.core import email_service
from app.core import sms_service
from app.core.request_context import resolve_client_ip
from app.core.password_utils import generate_strong_password

# 2fa
from typing import Optional, Union
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    LoginStep2Response,
    MustChangePasswordResponse,
    TOTPLoginRequest,
)
from app.crud import two_factor as crud_2fa
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_2fa_session_token,
)
from app.core.encryption import decrypt_data

# probando rate limitng
from app.rate_limiting import limiter

# cookies
from app.crud.auth import set_refresh_cookie, clear_refresh_cookie

# redis
from redis.asyncio import Redis
from app.db.cache import get_cache_client
from app.crud import audit as crud_audit
from app.core import policia
from app.core.rsa_manager import RSAManager
from app.core.enums import AuditEvent
from app.core.security import verify_password
from app.crud import permission as crud_permission

# recaptcha
from app.core.recaptcha import verify_recaptcha, is_valid_recaptcha

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/public-key")
def get_public_key():
    """
    Retorna la llave pública RSA del día para cifrar datos sensibles en el cliente.
    """
    _, public_key_pem = RSAManager.get_keys()
    return {"public_key": public_key_pem}


def _get_role_claim(user: User) -> str | None:
    if user.role:
        return user.role.name
    return None


def _issue_tokens_for_user(user, db: Session):
    extra_claims = {"role": _get_role_claim(user)} if _get_role_claim(user) else None
    access_token = create_access_token(subject=user.id, extra_claims=extra_claims)

    rt = create_refresh_token(subject=user.id)
    crud_token.create_refresh_token_record(
        db,
        user_id=user.id,
        jti=rt["jti"],
        expires_at=rt["expires_at"],
        device_info=rt.get("device_info"),
    )

    return access_token, rt["token"]


# crud_user.create_public_user ya maneja IntegrityError y lanza un HTTPException 409
@router.post("/register", response_model=UserCreateResponse, status_code=201)
async def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    # 0. Verificar reCAPTCHA v2 server-side si esta requerido por entorno.
    if settings.REQUIRE_RECAPTCHA:
        if not user_in.recaptcha_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verificacion de seguridad requerida.",
            )
        client_ip = request.client.host if request.client else None
        recaptcha_result = await verify_recaptcha(user_in.recaptcha_token, client_ip)
        if not is_valid_recaptcha(recaptcha_result):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verificación de seguridad fallida. Intenta nuevamente.",
            )
    # 1. Intentar descifrar la contraseña si viene cifrada (RSA)
    if user_in.password and not user_in.generate_password:
        try:
            decrypted_password = RSAManager.decrypt_password(user_in.password)
            user_in.password = decrypted_password
        except Exception as e:
            # Forzamos el cifrado según requerimiento
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error de seguridad: La contraseña debe estar cifrada con la llave del día.",
            )

    # Si el cliente solicita generación, creamos una segura.
    data = user_in.model_dump()
    generate_flag = data.get("generate_password", False)
    generated_password = None

    if generate_flag:
        generated_password = generate_strong_password()
        data["password"] = generated_password

    # Reconstruir el modelo para que corran validadores de fuerza sobre la contraseña ya descifrada
    try:
        user_in_with_password = UserCreate(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user_in_with_password.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El telefono es requerido para verificar la cuenta por SMS.",
        )

    user_in_with_password.username = crud_user.normalize_user_id(user_in_with_password.username)
    logger.debug("Iniciando registro para username: %s", user_in_with_password.username)
    existing_user_email = (
        crud_user.get_user_by_email(db, email=user_in_with_password.email)
        if user_in_with_password.email
        else None
    )
    existing_user_username = crud_user.get_user_by_username(db, username=user_in_with_password.username)
    existing_user_phone = (
        crud_user.get_user_by_phone(db, phone_number=user_in_with_password.phone_number)
        if user_in_with_password.phone_number
        else None
    )
    
    existing_user = existing_user_email or existing_user_username or existing_user_phone

    if existing_user:
        logger.debug(f"Usuario ya existe: email={existing_user.email}, username={existing_user.username}, verificado={existing_user.phone_verified}")
        if not existing_user.phone_verified:
            logger.info(f"Reenviando SMS de verificación a {existing_user.phone_number}")
            try:
                code = crud_user.create_sms_otp(db, existing_user, "verify_phone")
                await sms_service.send_otp(existing_user.phone_number, code, "verify_phone")
                logger.info(f"SMS de verificación reenviado a {existing_user.phone_number}")
            except Exception as e:
                logger.error(
                    f"Error reenviando SMS de verificación a {existing_user.phone_number}: {str(e)}",
                    exc_info=True
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "ACCOUNT_UNVERIFIED",
                    "phone_number": existing_user.phone_number
                },
            )
        else:
            # Si ya está verificado, es un conflicto normal (409)
            conflict_detail = "Usuario, telefono o email ya registrado"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflict_detail,
            )

    try:
        user = crud_user.create_public_user(db=db, user_in=user_in_with_password)
        logger.info("Usuario creado exitosamente: id=%s", user.id)
    except Exception as e:
        logger.error(f"Error al crear usuario en BD: {str(e)}")
        raise e

    # 2. Enviar SMS de verificacion.
    try:
        logger.debug("Intentando enviar SMS de verificacion a %s", user.phone_number)
        code = crud_user.create_sms_otp(db, user, "verify_phone")
        await sms_service.send_otp(user.phone_number, code, "verify_phone")
        logger.info("SMS de verificacion enviado a %s", user.phone_number)
    except Exception as e:
        logger.error(
            "Error enviando SMS de verificacion a %s: %s",
            user.phone_number,
            str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el SMS de verificacion.",
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "phone_number": user.phone_number,
        "phone_verified": user.phone_verified,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "role_id": user.role_id,
        "photo_url": user.photo_url,
        "created_at": user.created_at,
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK)
@router.post("/verify-phone", status_code=status.HTTP_200_OK)
async def verify_email(
    request: Request,
    body: EmailVerificationRequest,
    db: Session = Depends(get_db),
):


    user = crud_user.get_user_by_phone(db, phone_number=body.phone_number)
    is_code_valid = bool(user) and crud_user.verify_sms_otp(
        db, user, body.code, "verify_phone"
    )
    if not is_code_valid or not crud_user.mark_phone_verified(db, phone_number=body.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo SMS invalido o usuario no encontrado.",
        )
    return {"message": "Telefono verificado exitosamente. Ahora puedes iniciar sesion."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
@router.post("/resend-phone-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    db: Session = Depends(get_db),
):


    identifier = body.phone_number or body.email
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telefono o email requerido.",
        )

    user = crud_user.get_user_by_phone(db, phone_number=identifier)
    if not user:
        user = crud_user.get_user_by_email(db, email=identifier)

    if not user or user.phone_verified:
        return {"message": "Si la cuenta existe y no esta verificada, se ha enviado un nuevo codigo."}

    try:
        code = crud_user.create_sms_otp(db, user, "verify_phone")
        await sms_service.send_otp(user.phone_number, code, "verify_phone")
    except Exception:
        logger.exception("Error reenviando SMS de verificacion")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el SMS de verificacion.",
        )

    return {"message": "Codigo SMS reenviado exitosamente."}


@router.patch("/update-phone", status_code=status.HTTP_200_OK)
async def update_phone(
    request: Request,
    body: UpdatePhoneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Verificar si el teléfono ya existe
    existing_user = crud_user.get_user_by_phone(db, phone_number=body.phone_number)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El número de teléfono ya está registrado por otro usuario.",
        )

    # Actualizar teléfono y generar OTP
    try:
        code = crud_user.request_phone_update(db, current_user, body.phone_number)
        await sms_service.send_otp(body.phone_number, code, "verify_phone")
        return {"message": "Código de verificación enviado al nuevo número."}
    except Exception as e:
        logger.error(f"Error al solicitar actualización de teléfono: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el SMS de verificación.",
        )


# rate limiting
@router.post("/login", response_model=Union[TokenResponse, LoginStep2Response, MustChangePasswordResponse])
@limiter.limit("10/minute")
async def login(
    request: Request,
    # prueba redis
    background_tasks: BackgroundTasks,
    #
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
    cache: Redis = Depends(get_cache_client),
):
    # 0. Verificar reCAPTCHA v2 server-side si esta requerido por entorno.
    if settings.REQUIRE_RECAPTCHA:
        if not payload.recaptcha_token:
            background_tasks.add_task(
                crud_audit.create_audit_log,
                event=AuditEvent.LOGIN_FAILURE,
                attempted_email=payload.identifier,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verificacion de seguridad requerida.",
            )
        client_ip = resolve_client_ip(request)
        recaptcha_result = await verify_recaptcha(payload.recaptcha_token, client_ip)
        if not is_valid_recaptcha(recaptcha_result):
            background_tasks.add_task(
                crud_audit.create_audit_log,
                event=AuditEvent.LOGIN_FAILURE,
                attempted_email=payload.identifier,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Verificación de seguridad fallida. Intenta nuevamente.",
            )
    # 1. Descifrar contraseña RSA
    try:
        decrypted_password = RSAManager.decrypt_password(payload.password)
        payload.password = decrypted_password
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de seguridad: Credenciales no cifradas correctamente.",
        )

    # paso 1
    logger.debug(f"DEBUG LOGIN: Intentando login para: {payload.identifier}")
    user = crud_user.get_user_by_identifier(db, payload.identifier)
    # paso 2 manejar el usuario no encontrado
    if not user:
        logger.debug(f"DEBUG LOGIN: Usuario no encontrado en BD: {payload.identifier}")
        background_tasks.add_task(
            crud_audit.create_audit_log,
            # db,
            event=AuditEvent.LOGIN_FAILURE,
            attempted_email=payload.identifier,
        )
        # Incrementamos nuestro contador
        await policia.increment_login_failure(payload.identifier, cache)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
        )

    logger.debug(f"DEBUG LOGIN: Usuario encontrado: {user.email}, email_verified={user.email_verified}, is_active={user.is_active}")
    # el usuario existe ahora verificamos si no esta blqoueado
    if policia.is_account_locked(user):
        from datetime import datetime, timezone
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        remaining = locked_until - datetime.now(timezone.utc)
        minutes_left = max(1, int(remaining.total_seconds() / 60))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cuenta bloqueada temporalmente. Intente nuevamente en {minutes_left} minuto(s).",
        )
    # el usuario existe ya aparte no esta bloqueado, vemos la contraseña
    if not verify_password(payload.password, user.hashed_password):
        # Contraseña incorrecta.
        background_tasks.add_task(
            crud_audit.create_audit_log,
            # db,
            event=AuditEvent.LOGIN_FAILURE,
            user_id=user.id,
            attempted_email=user.email,
        )

        await policia.increment_login_failure(payload.identifier, cache)

        failures = await policia.get_login_failures(payload.identifier, cache)
        if failures >= policia.MAX_FAILED_ATTEMPTS:
            background_tasks.add_task(policia.lock_account, user_id=user.id)
            await policia.clear_login_failures(payload.identifier, cache)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
        )
    # contraseña correcta vemos si esta verificado
    logger.debug(f"DEBUG LOGIN: Verificando email_verified para {user.email}: {user.email_verified}")
    if not user.phone_verified:
        logger.info(f"Intento de login para usuario no verificado: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "ACCOUNT_UNVERIFIED",
                "phone_number": user.phone_number,
                "message": "Tu cuenta no ha sido verificada. Por favor, verifica tu telefono."
            },
        )

    # vemos si esta activo
    if not user.is_active:
        logger.info(f"Intento de login para usuario inactivo: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo. Contacte al administrador."
        )
    # limpiadmor contadores redis
    await policia.clear_login_failures(payload.identifier, cache)
    # comprobamos 2fa (antes que must_change_password)
    if user.is_totp_enabled:
        if user.phone_number:
            try:
                code = crud_user.create_sms_otp(db, user, "login_2fa")
                await sms_service.send_otp(user.phone_number, code, "login_2fa")
            except Exception:
                logger.exception("Error enviando SMS OTP para 2FA")
        session_token = create_2fa_session_token(subject=user.id)
        return LoginStep2Response(session_token=session_token)
    # comprobamos si debe cambiar contraseña
    if user.must_change_password:
        reset_token = crud_token.create_password_reset_token(db, user.id)
        if user.phone_number:
            try:
                code = crud_user.create_sms_otp(db, user, "reset_password")
                await sms_service.send_otp(user.phone_number, code, "reset_password")
            except Exception:
                logger.exception("Error enviando SMS OTP para cambio de contraseña")
        return MustChangePasswordResponse(reset_token=reset_token)
    # comprobamos si la contraseña expiró
    if crud_user.is_password_expired(user):
        reset_token = crud_token.create_password_reset_token(db, user.id)
        if user.phone_number:
            try:
                code = crud_user.create_sms_otp(db, user, "reset_password")
                await sms_service.send_otp(user.phone_number, code, "reset_password")
            except Exception:
                logger.exception("Error enviando SMS OTP para cambio de contraseña")
        return MustChangePasswordResponse(reset_token=reset_token)
    # login exitoso
    background_tasks.add_task(
        crud_audit.create_audit_log,
        # db,
        event=AuditEvent.LOGIN_SUCCESS,
        user_id=user.id,
        attempted_email=user.email,
    )

    access_token, refresh_token = _issue_tokens_for_user(user, db)
    #
    set_refresh_cookie(response, refresh_token)
    # return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    return TokenResponse(access_token=access_token, token_type="bearer")


# 2fA
@router.post("/2fa/verify-login", response_model=Union[TokenResponse, MustChangePasswordResponse])
async def verify_login_2fa(
    body: TOTPLoginRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    cache: Redis = Depends(get_cache_client),
):
    # verficamos token y codigo 2fa

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de sesion 2FA invalido",
    )

    try:
        payload = jwt.decode(
            body.session_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "pre_2fa":
            raise credentials_exception
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 2. Obtener el usuario
    user = crud_user.get_user(db, email)
    if not user or not user.is_active or not user.is_totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no válido para 2FA"
        )

    # 3. Verificar el codigo
    is_code_valid = False

    if len(body.code) == 6:
        try:
            secret = decrypt_data(user.totp_secret)
            is_code_valid = crud_2fa.verify_totp_code(secret, body.code)
        except Exception:
            is_code_valid = False
        if not is_code_valid:
            is_code_valid = crud_user.verify_sms_otp(db, user, body.code, "login_2fa")
    else:
        is_code_valid = crud_2fa.validate_backup_code(db, user, body.code)

    if not is_code_valid:
        background_tasks.add_task(
            crud_audit.create_audit_log,
            # db,
            event=AuditEvent.LOGIN_FAILURE,
            user_id=user.id,
            attempted_email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Codigo 2fa invalido"
        )

    background_tasks.add_task(
        crud_audit.create_audit_log,
        # db,
        event=AuditEvent.V2P_SUCCESS,
        user_id=user.id,
        attempted_email=user.email,
    )

    await policia.clear_login_failures(user.id, cache)

    if user.must_change_password:
        reset_token = crud_token.create_password_reset_token(db, user.id)
        if user.phone_number:
            try:
                code = crud_user.create_sms_otp(db, user, "reset_password")
                await sms_service.send_otp(user.phone_number, code, "reset_password")
            except Exception:
                logger.exception("Error enviando SMS OTP para cambio de contraseña")
        return MustChangePasswordResponse(reset_token=reset_token)
    if crud_user.is_password_expired(user):
        reset_token = crud_token.create_password_reset_token(db, user.id)
        if user.phone_number:
            try:
                code = crud_user.create_sms_otp(db, user, "reset_password")
                await sms_service.send_otp(user.phone_number, code, "reset_password")
            except Exception:
                logger.exception("Error enviando SMS OTP para cambio de contraseña")
        return MustChangePasswordResponse(reset_token=reset_token)

    access_token, refresh_token = _issue_tokens_for_user(user, db)
    set_refresh_cookie(response, refresh_token)

    return TokenResponse(access_token=access_token, token_type="bearer")


"""
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Token nvalido")
        jti, sub = decoded.get("jti"), decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    if not crud_token.is_refresh_token_valid(db, jti):
        raise HTTPException(status_code=401, detail="Refresh token invalido o revocado")

    crud_token.revoke_refresh_token_by_jti(db, jti)

    user = crud_user.get_user(db, sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    access_token, refresh_token = _issue_tokens_for_user(user, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
"""


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="No se encontro refresh token")

    try:
        decoded = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Token invalido")
        jti, sub = decoded.get("jti"), decoded.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    if not crud_token.is_refresh_token_valid(db, jti):
        raise HTTPException(status_code=401, detail="Refresh token inalido")

    crud_token.revoke_refresh_token_by_jti(db, jti)
    user = crud_user.get_user(db, sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    new_access_token, new_refresh_token = _issue_tokens_for_user(user, db)
    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(access_token=new_access_token, token_type="bearer")


""""
@router.post("/logout")
def logout(body: TokenRefreshRequest, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    try:
        decoded = jwt.decode(body.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        jti = decoded.get("jti")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token invalido")

    crud_token.revoke_refresh_token_by_jti(db, jti)
    return {"msg": "logout OK"}
"""


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(None),
    current_user: User = Depends(get_current_active_user),
):
    if refresh_token:
        try:
            decoded = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            jti = decoded.get("jti")
            if jti:
                crud_token.revoke_refresh_token_by_jti(db, jti)
        except JWTError:
            pass
    clear_refresh_cookie(response)

    return {"msg": "logout OK"}


@router.get("/me", response_model=UserOut)
@router.get("/me", response_model=UserProfileOut)
def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "phone_number": current_user.phone_number,
        "phone_verified": current_user.phone_verified,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "role_id": current_user.role_id,
        "photo_url": current_user.photo_url,
        "created_at": current_user.created_at,
        "permissions": crud_permission.get_effective_permission_codes(
            db, current_user.id
        ),
    }


# endpoints reset password
@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = crud_user.get_user_by_identifier(db, body.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una cuenta con ese usuario o telefono.",
        )
    if not user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tu cuenta no tiene un numero de celular registrado para recuperar contrasena.",
        )

    try:
        code = crud_user.create_sms_otp(db, user, "reset_password")
        await sms_service.send_otp(user.phone_number, code, "reset_password")
    except Exception as e:
        logger.error(f"Error al enviar SMS OTP de recuperacion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el codigo SMS. Intenta nuevamente.",
        )

    # Ocultar parcialmente el número para mayor privacidad (ej. ******123)
    masked_phone = f"******{user.phone_number[-4:]}" if len(user.phone_number) >= 4 else user.phone_number
    return {"msg": f"Se envio un codigo SMS de recuperacion a tu numero {masked_phone}"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest, 
    response: Response,
    db: Session = Depends(get_db)
):
    user = crud_user.get_user_by_identifier(db, body.identifier)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if not crud_user.verify_sms_otp(db, user, body.code, "reset_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo SMS invalido o expirado.",
        )

    # Decodificar contraseña si viene encriptada con RSA
    decrypted_password = body.new_password
    if len(body.new_password) > 100:
        try:
            decrypted_password = RSAManager.decrypt_password(body.new_password)
        except Exception as e:
            logger.warning(f"Error decrypting reset password with RSA, trying as plain text: {str(e)}")

    if crud_user.is_password_in_history(db, user, decrypted_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes reutilizar una contrasena que ya has usado anteriormente.",
        )

    crud_user.update_password(db, db_user=user, new_password=decrypted_password)

    if user.must_change_password:
        user.must_change_password = False
        db.add(user)
        db.commit()

        if user.is_totp_enabled:
            return {"msg": "Contrasena actualizada exitosamente. Inicia sesion nuevamente."}

        access_token, refresh_token = _issue_tokens_for_user(user, db)
        set_refresh_cookie(response, refresh_token)
        return TokenResponse(access_token=access_token, token_type="bearer")

    return {"msg": "Contrasena actualizada exitosamente."}


# put user
@router.put("/update-profile", response_model=UserOut)
@router.put("/update-profile", response_model=UserProfileOut)
async def update_users_me(
    user_in: UserUpdateProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    if user_in.email and user_in.email != current_user.email:
        if not user_in.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes confirmar tu contraseña para cambiar el correo electrónico",
            )
        if not verify_password(user_in.password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Contraseña incorrecta",
            )
        existing_user_with_new_email = crud_user.get_user_by_email(
            db, email=user_in.email
        )
        if existing_user_with_new_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este correo electronico ya esta registrado por otro usuario",
            )

    updated_user = crud_user.update_own_profile(
        db=db, db_user_to_update=current_user, user_in=user_in
    )
    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "username": updated_user.username,
        "phone_number": updated_user.phone_number,
        "phone_verified": updated_user.phone_verified,
        "is_active": updated_user.is_active,
        "is_admin": updated_user.is_admin,
        "role_id": updated_user.role_id,
        "photo_url": updated_user.photo_url,
        "created_at": updated_user.created_at,
        "permissions": crud_permission.get_effective_permission_codes(
            db, updated_user.id
        ),
    }
