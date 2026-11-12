import logging
from typing import Optional, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.core import policia
from app.core.config import settings
from app.core.dependencies import (
    get_current_active_user,
    get_current_user_allow_change,
)
from app.core.email_service import send_password_reset_email
from app.core.enums import AuditAction, AuditEntity
from app.core.security import verify_password
from app.crud import permission as crud_permission
from app.crud import token as crud_token
from app.crud import user as crud_user
from app.db.cache import get_cache_client
from app.db.session import get_db
from app.models.security import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginStep2Response,
    MessageResponse,
    MustChangePasswordResponse,
    ResetPasswordRequest,
    TokenResponse,
    TOTPLoginRequest,
)
from app.schemas.two_factor import (
    TOTPBackupCodesResponse,
    TOTPDisableRequest,
    TOTPSetupResponse,
    TOTPStatusResponse,
    TOTPVerifyRequest,
)
from app.schemas.user import UserProfileOut, UserUpdateProfile
from app.services import audit as audit_service
from app.services import auth as auth_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _profile(db: Session, user: User) -> UserProfileOut:
    profile = UserProfileOut.model_validate(user)
    profile.permissions = crud_permission.get_effective_permission_codes(db, user.id)
    return profile


def _device_info(request: Request) -> Optional[str]:
    user_agent = request.headers.get("user-agent")
    return user_agent[:300] if user_agent else None


def _audit_failure(
    background_tasks: BackgroundTasks,
    request: Request,
    *,
    email: str,
    reason: str,
    user_id: Optional[int] = None,
    action: AuditAction = AuditAction.LOGIN_FAILURE,
) -> None:
    background_tasks.add_task(
        audit_service.log_event,
        action=action,
        entity=AuditEntity.AUTH,
        entity_id=user_id,
        details={"email": email, "reason": reason},
        user_id=user_id,
        request=request,
    )


@router.post(
    "/login",
    response_model=Union[
        TokenResponse,
        LoginStep2Response,
        MustChangePasswordResponse,
    ],
)
async def login(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    payload: LoginRequest,
    db: Session = Depends(get_db),
    cache: Redis | None = Depends(get_cache_client),
):
    email = crud_user.normalize_email(payload.email)
    user = crud_user.get_user_by_email(db, email)

    if not user:
        await policia.increment_login_failure(email, cache)
        _audit_failure(
            background_tasks,
            request,
            email=email,
            reason="user_not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    user_id = user.id
    user_email = user.email

    if not verify_password(payload.password, user.password_hash):
        if not policia.is_account_locked(user):
            crud_user.increment_failed_attempts(db, user)
            db.commit()
        await policia.increment_login_failure(email, cache)
        _audit_failure(
            background_tasks,
            request,
            email=user_email,
            reason="invalid_password",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        _audit_failure(
            background_tasks,
            request,
            email=user_email,
            reason="inactive_user",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador.",
        )

    if policia.is_account_locked(user):
        minutes = policia.remaining_lockout_minutes(user)
        _audit_failure(
            background_tasks,
            request,
            email=user_email,
            reason="account_locked",
            user_id=user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Cuenta bloqueada temporalmente. "
                f"Intenta nuevamente en {minutes} minuto(s)."
            ),
        )

    crud_user.reset_failed_attempts(db, user)
    db.commit()
    await policia.clear_login_failures(email, cache)

    if user.is_totp_enabled:
        session_token = auth_service.create_two_factor_session_token(user)
        background_tasks.add_task(
            audit_service.log_event,
            action=AuditAction.LOGIN_2FA_REQUIRED,
            entity=AuditEntity.AUTH,
            entity_id=user_id,
            details={"email": user_email},
            user_id=user_id,
            request=request,
        )
        return LoginStep2Response(session_token=session_token)

    if user.must_change_password:
        change_token = auth_service.create_change_token(user)
        background_tasks.add_task(
            audit_service.log_event,
            action=AuditAction.LOGIN_CHANGE_PASSWORD_REQUIRED,
            entity=AuditEntity.AUTH,
            entity_id=user_id,
            details={"email": user_email},
            user_id=user_id,
            request=request,
        )
        return MustChangePasswordResponse(change_token=change_token)

    access_token, refresh_token = auth_service.issue_tokens(
        db,
        user,
        device_info=_device_info(request),
    )
    crud_user.mark_login_success(db, user)
    db.commit()
    auth_service.set_refresh_cookie(response, refresh_token)

    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.LOGIN_SUCCESS,
        entity=AuditEntity.AUTH,
        entity_id=user_id,
        details={"email": user_email},
        user_id=user_id,
        request=request,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/2fa/verify-login",
    response_model=Union[TokenResponse, MustChangePasswordResponse],
)
async def verify_login_2fa(
    body: TOTPLoginRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    cache: Redis | None = Depends(get_cache_client),
):
    try:
        user = auth_service.verify_two_factor_session(db, body.session_token)
    except HTTPException:
        _audit_failure(
            background_tasks,
            request,
            email="",
            reason="invalid_2fa_session",
            action=AuditAction.LOGIN_2FA_FAILURE,
        )
        raise

    if policia.is_account_locked(user):
        _audit_failure(
            background_tasks,
            request,
            email=user.email,
            reason="account_locked",
            user_id=user.id,
            action=AuditAction.LOGIN_2FA_FAILURE,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta bloqueada temporalmente",
        )

    if not auth_service.validate_two_factor_code(db, user, body.code):
        crud_user.increment_failed_attempts(db, user)
        db.commit()
        _audit_failure(
            background_tasks,
            request,
            email=user.email,
            reason="invalid_2fa_code",
            user_id=user.id,
            action=AuditAction.LOGIN_2FA_FAILURE,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código 2FA inválido",
        )

    user_id = user.id
    user_email = user.email
    crud_user.reset_failed_attempts(db, user)
    await policia.clear_login_failures(user_email, cache)

    if user.must_change_password:
        change_token = auth_service.create_change_token(user)
        db.commit()
        background_tasks.add_task(
            audit_service.log_event,
            action=AuditAction.LOGIN_CHANGE_PASSWORD_REQUIRED,
            entity=AuditEntity.AUTH,
            entity_id=user_id,
            details={"email": user_email, "two_factor": True},
            user_id=user_id,
            request=request,
        )
        return MustChangePasswordResponse(change_token=change_token)

    access_token, refresh_token = auth_service.issue_tokens(
        db,
        user,
        device_info=_device_info(request),
    )
    crud_user.mark_login_success(db, user)
    db.commit()
    auth_service.set_refresh_cookie(response, refresh_token)

    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.LOGIN_2FA_SUCCESS,
        entity=AuditEntity.AUTH,
        entity_id=user_id,
        details={"email": user_email},
        user_id=user_id,
        request=request,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    refresh_token: Optional[str] = Cookie(
        None,
        alias=settings.REFRESH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontró el refresh token",
        )

    try:
        access_token, new_refresh_token = auth_service.refresh_session(
            db, refresh_token
        )
    except HTTPException:
        db.rollback()
        auth_service.clear_refresh_cookie(response)
        raise

    db.commit()
    auth_service.set_refresh_cookie(response, new_refresh_token)
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.TOKEN_REFRESH,
        entity=AuditEntity.AUTH,
        request=request,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    refresh_token: Optional[str] = Cookie(
        None,
        alias=settings.REFRESH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
):
    if refresh_token:
        auth_service.revoke_session(db, refresh_token)
        db.commit()
    auth_service.clear_refresh_cookie(response)
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.LOGOUT,
        entity=AuditEntity.AUTH,
        request=request,
    )
    return MessageResponse(message="Sesión cerrada correctamente")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    crud_token.revoke_all_user_tokens(db, current_user.id)
    db.commit()
    auth_service.clear_refresh_cookie(response)
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.LOGOUT_ALL,
        entity=AuditEntity.AUTH,
        entity_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(message="Todas las sesiones fueron cerradas")


@router.get("/me", response_model=UserProfileOut)
def read_me(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return _profile(db, current_user)


@router.patch("/me", response_model=UserProfileOut)
def update_me(
    payload: UserUpdateProfile,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        crud_user.update_user(db, current_user, {"full_name": payload.full_name})
        db.commit()
        background_tasks.add_task(
            audit_service.log_event,
            action=AuditAction.USER_UPDATE,
            entity=AuditEntity.USER,
            entity_id=current_user.id,
            details={"full_name": payload.full_name},
            user_id=current_user.id,
            request=request,
        )
    return _profile(db, current_user)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user_allow_change),
    db: Session = Depends(get_db),
):
    auth_service.change_password(
        db,
        current_user,
        payload.current_password,
        payload.new_password,
    )
    db.commit()
    auth_service.clear_refresh_cookie(response)
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PASSWORD_CHANGE,
        entity=AuditEntity.AUTH,
        entity_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(
        message="Contraseña actualizada. Inicia sesión nuevamente."
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    result = auth_service.request_password_reset(db, payload.email)
    generic_message = (
        "Si el correo existe, recibirás un enlace para restablecer la contraseña."
    )
    if not result:
        background_tasks.add_task(
            audit_service.log_event,
            action=AuditAction.PASSWORD_RESET_REQUEST,
            entity=AuditEntity.AUTH,
            details={"email": crud_user.normalize_email(payload.email), "found": False},
            request=request,
        )
        return MessageResponse(message=generic_message)

    raw_token, user = result
    db.commit()
    try:
        await send_password_reset_email(user.email, raw_token, user.full_name)
    except Exception:
        logger.exception("No se pudo enviar el correo de recuperación")
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PASSWORD_RESET_REQUEST,
        entity=AuditEntity.AUTH,
        entity_id=user.id,
        details={"email": user.email, "found": True},
        user_id=user.id,
        request=request,
    )
    return MessageResponse(message=generic_message)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user = auth_service.reset_password(db, payload.token, payload.new_password)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.PASSWORD_RESET,
        entity=AuditEntity.AUTH,
        entity_id=user.id,
        user_id=user.id,
        request=request,
    )
    return MessageResponse(
        message="Contraseña restablecida. Inicia sesión nuevamente."
    )


@router.get("/2fa/status", response_model=TOTPStatusResponse)
def two_factor_status(
    current_user: User = Depends(get_current_active_user),
):
    return TOTPStatusResponse(
        is_enabled=current_user.is_totp_enabled,
        enabled_at=current_user.totp_enabled_at,
    )


@router.post("/2fa/setup", response_model=TOTPSetupResponse)
def two_factor_setup(
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    secret, uri = auth_service.setup_totp(db, current_user)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.TOTP_SETUP,
        entity=AuditEntity.AUTH,
        entity_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
    return TOTPSetupResponse(secret=secret, otpauth_uri=uri)


@router.post("/2fa/enable", response_model=TOTPBackupCodesResponse)
def two_factor_enable(
    payload: TOTPVerifyRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    backup_codes = auth_service.enable_totp(db, current_user, payload.totp_code)
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.TOTP_ENABLE,
        entity=AuditEntity.AUTH,
        entity_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
    return TOTPBackupCodesResponse(backup_codes=backup_codes)


@router.post("/2fa/disable", response_model=MessageResponse)
def two_factor_disable(
    payload: TOTPDisableRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    auth_service.disable_totp(
        db,
        current_user,
        payload.password,
        payload.totp_code,
    )
    db.commit()
    background_tasks.add_task(
        audit_service.log_event,
        action=AuditAction.TOTP_DISABLE,
        entity=AuditEntity.AUTH,
        entity_id=current_user.id,
        user_id=current_user.id,
        request=request,
    )
    return MessageResponse(message="2FA deshabilitado correctamente")