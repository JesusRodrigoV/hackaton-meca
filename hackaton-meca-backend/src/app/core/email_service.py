import logging
import httpx
from pydantic import EmailStr
from app.core.config import settings
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

logger = logging.getLogger(__name__)

# Configuración SMTP
logger.debug("Iniciando email_service con MAIL_SERVER=%s, MAIL_PORT=%s, MAIL_FROM=%s", settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_FROM)
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME
)


async def _send_email_via_smtp(email_to: str, subject: str, html_body: str) -> None:
    """Envía un email usando SMTP (fastapi-mail)."""
    logger.debug("Configurando envio de email a %s", email_to)
    logger.debug("MAIL_SERVER=%s, MAIL_PORT=%s, MAIL_FROM=%s", settings.MAIL_SERVER, settings.MAIL_PORT, settings.MAIL_FROM)
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_body,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        logger.info("Correo enviado a %s via SMTP (%s)", email_to, settings.MAIL_SERVER)
    except Exception as e:
        logger.exception("Fallo al enviar correo a %s", email_to)
        raise


async def _send_email_via_postmark(email_to: str, subject: str, html_body: str) -> None:
    """Envía un email usando la API de Postmark (HTTPS - compatible con Render)."""
    # Mantenemos esto por si acaso, pero el default ahora será SMTP
    url = "https://api.postmarkapp.com/email"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": settings.POSTMARK_SERVER_TOKEN,
    }
    payload = {
        "From": f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>",
        "To": email_to,
        "Subject": subject,
        "HtmlBody": html_body,
        "MessageStream": "outbound",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code not in (200, 202):
            raise Exception(f"Postmark error {response.status_code}: {response.text}")
    logger.info("Correo enviado a %s via Postmark", email_to)


async def send_password_reset_email(email_to: EmailStr, token: str, username: str):
    reset_url = f"{settings.FRONTEND_RESET_PASSWORD_URL}?token={token}"
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; line-height: 1.6; }}
            .container {{ width: 90%; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
            p {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3>Hola, {username}</h3>
            <p>Recibimos una solicitud para restablecer tu contraseña en ZooConnect.</p>
            <p>Si no hiciste esta solicitud, puedes ignorar este correo de forma segura.</p>
            <p>
                Haz clic en el siguiente botón para establecer una nueva contraseña.
                Este enlace expirará en <strong>{settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos</strong>.
            </p>
            <p>
                <a href="{reset_url}" class="button">Restablecer Contraseña</a>
            </p>
            <p style="margin-top: 30px; font-size: 0.9em; color: #555;">
                Si el botón no funciona, copia y pega esta URL en tu navegador:
                <br>
                <a href="{reset_url}">{reset_url}</a>
            </p>
        </div>
    </body>
    </html>
    """
    await _send_email_via_smtp(
        email_to, "Restablece tu contraseña de ZooConnect", html_template
    )
    logger.info("Correo de reset enviado a %s", email_to)


async def send_generated_password_email(
    email_to: EmailStr, password: str, username: str
):
    """Envía la contraseña generada al usuario."""
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; line-height: 1.6; }}
            .container {{ width: 90%; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .password {{ font-family: monospace; background:#f6f6f6; padding:8px; border-radius:4px; display:inline-block }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3>Hola, {username}</h3>
            <p>Tu cuenta en ZooConnect fue creada y se generó una contraseña segura para ti.</p>
            <p>Contraseña temporal: <span class="password">{password}</span></p>
            <p>Te recomendamos iniciar sesión y cambiar la contraseña inmediatamente.</p>
        </div>
    </body>
    </html>
    """
    await _send_email_via_smtp(
        email_to, "Tu contraseña temporal de ZooConnect", html_template
    )
    logger.info("Correo con contrasena generada enviado a %s", email_to)


async def send_verification_email(email_to: EmailStr, code: str, username: str):
    """Envía el código de verificación al usuario tras el registro."""
    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
            .container {{ width: 90%; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ padding: 20px; }}
            .code {{ font-size: 24px; font-weight: bold; color: #4CAF50; letter-spacing: 5px; text-align: center; margin: 20px 0; padding: 10px; background: #f9f9f9; border: 1px dashed #4CAF50; }}
            .footer {{ font-size: 0.8em; color: #777; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Bienvenido a ZooConnect</h2>
            </div>
            <div class="content">
                <h3>Hola, {username}</h3>
                <p>Gracias por registrarte. Para activar tu cuenta, por favor usa el siguiente código de verificación:</p>
                <div class="code">{code}</div>
                <p>Si no creaste esta cuenta, puedes ignorar este correo.</p>
            </div>
            <div class="footer">
                &copy; 2024 ZooConnect - Gestión de Zoológicos
            </div>
        </div>
    </body>
    </html>
    """
    await _send_email_via_smtp(
        email_to, "Activa tu cuenta de ZooConnect", html_template
    )
    logger.info("Correo de verificacion enviado a %s", email_to)