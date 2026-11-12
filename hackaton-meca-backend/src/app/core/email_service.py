import html
import logging
from urllib.parse import quote

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)


def _connection_config() -> ConnectionConfig:
    if not settings.MAIL_SERVER:
        raise RuntimeError("MAIL_SERVER no está configurado")
    return ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
        VALIDATE_CERTS=True,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    )


async def send_email(email_to: EmailStr, subject: str, html_body: str) -> None:
    if not settings.MAIL_ENABLED:
        logger.warning("MAIL_ENABLED=false; se omite el envío a %s", email_to)
        return

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_body,
        subtype=MessageType.html,
    )
    try:
        await FastMail(_connection_config()).send_message(message)
        logger.info("Correo enviado a %s", email_to)
    except Exception:
        logger.exception("No se pudo enviar correo a %s", email_to)
        raise


def _layout(title: str, greeting: str, body: str, button_text: str | None = None, button_url: str | None = None) -> str:
    button = ""
    if button_text and button_url:
        button = (
            f'<p><a href="{button_url}" '
            'style="background:#1f6f43;color:#fff;padding:10px 18px;'
            'text-decoration:none;border-radius:6px;display:inline-block">'
            f"{html.escape(button_text)}</a></p>"
            f'<p style="font-size:12px;color:#555">Si el botón no funciona, '
            f'copia este enlace: <a href="{button_url}">{button_url}</a></p>'
        )
    return f"""
    <html>
      <body style="font-family:Arial,sans-serif;line-height:1.6;color:#222">
        <div style="max-width:620px;margin:0 auto;padding:24px;border:1px solid #ddd;border-radius:8px">
          <h2 style="color:#1f6f43">{html.escape(title)}</h2>
          <p>{greeting}</p>
          {body}
          {button}
          <p style="margin-top:28px;font-size:12px;color:#666">
            Este mensaje fue generado automáticamente por Enseña por Bolivia.
          </p>
        </div>
      </body>
    </html>
    """


def _reset_url(token: str) -> str:
    base = settings.FRONTEND_RESET_PASSWORD_URL
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}token={quote(token)}"


async def send_password_reset_email(
    email_to: EmailStr,
    token: str,
    full_name: str,
) -> None:
    reset_url = _reset_url(token)
    body = _layout(
        title="Restablece tu contraseña",
        greeting=f"Hola, {html.escape(full_name)}.",
        body=(
            "<p>Recibimos una solicitud para restablecer tu contraseña en Enseña por Bolivia.</p>"
            "<p>Si no realizaste esta solicitud, puedes ignorar este correo.</p>"
            f"<p>El enlace expira en <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos</strong>.</p>"
        ),
        button_text="Restablecer contraseña",
        button_url=reset_url,
    )
    await send_email(email_to, "Restablece tu contraseña - Enseña por Bolivia", body)


async def send_generated_password_email(
    email_to: EmailStr,
    password: str,
    full_name: str,
) -> None:
    body = _layout(
        title="Tu cuenta de Enseña por Bolivia fue creada",
        greeting=f"Hola, {html.escape(full_name)}.",
        body=(
            "<p>Un administrador creó tu cuenta institucional.</p>"
            "<p>Contraseña temporal: "
            f'<strong style="font-family:monospace">{html.escape(password)}</strong></p>'
            "<p>Al iniciar sesión deberás cambiarla antes de continuar.</p>"
        ),
    )
    await send_email(email_to, "Tu cuenta de Enseña por Bolivia fue creada", body)