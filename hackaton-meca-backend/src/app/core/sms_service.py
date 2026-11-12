import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SmsServiceNotConfigured(RuntimeError):
    pass


def _assert_textbee_configured() -> None:
    if not (settings.TEXTBEE_API_KEY and settings.TEXTBEE_DEVICE_ID):
        raise SmsServiceNotConfigured("TextBee no esta configurado")


def _device_url(path: str) -> str:
    base_url = settings.TEXTBEE_API_BASE_URL.rstrip("/")
    return f"{base_url}/gateway/devices/{settings.TEXTBEE_DEVICE_ID}/{path.lstrip('/')}"


async def send_sms(phone_number: str, message: str) -> dict:
    _assert_textbee_configured()
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _device_url("send-sms"),
            json={"recipients": [phone_number], "message": message},
            headers={"x-api-key": settings.TEXTBEE_API_KEY},
        )

    if response.status_code not in (200, 201, 202):
        logger.error("TextBee send failed: %s %s", response.status_code, response.text)
        raise RuntimeError("No se pudo enviar el SMS")

    response_data = response.json()
    logger.info("TextBee send successful: %s", response_data)
    return response_data


async def send_otp(phone_number: str, code: str, purpose: str) -> dict:
    purpose_text = {
        "verify_phone": "verificar tu cuenta",
        "reset_password": "restablecer tu contrasena",
        "login_2fa": "confirmar tu inicio de sesion",
        "change_password": "cambiar tu contrasena",
    }.get(purpose, "confirmar la operacion")
    message = f"ZooConnect: tu codigo para {purpose_text} es {code}. Expira en {settings.SMS_OTP_EXPIRE_MINUTES} minutos."
    return await send_sms(phone_number, message)


async def get_sms_status(sms_id: str) -> dict:
    _assert_textbee_configured()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _device_url(f"sms/{sms_id}"),
            headers={"x-api-key": settings.TEXTBEE_API_KEY},
        )

    if response.status_code != 200:
        logger.error("TextBee status failed: %s %s", response.status_code, response.text)
        raise RuntimeError("No se pudo consultar el SMS")

    return response.json()


async def get_sms_batch_status(batch_id: str) -> dict:
    _assert_textbee_configured()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _device_url(f"sms-batch/{batch_id}"),
            headers={"x-api-key": settings.TEXTBEE_API_KEY},
        )

    if response.status_code != 200:
        logger.error("TextBee batch status failed: %s %s", response.status_code, response.text)
        raise RuntimeError("No se pudo consultar el lote de SMS")

    return response.json()

