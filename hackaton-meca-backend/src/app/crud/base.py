import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def handle_integrity_error(
    db: Session,
    e: IntegrityError,
    detail: str = "Conflicto de datos",
    status_code: int = status.HTTP_409_CONFLICT,
):
    db.rollback()
    logger.exception("IntegrityError: %s - %s", detail, e)
    raise HTTPException(status_code=status_code, detail=detail)


def handle_db_error(
    db: Session,
    e: Exception,
    detail: str = "Error interno del servidor",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
):
    db.rollback()
    logger.exception("Error de base de datos: %s", detail)
    raise HTTPException(status_code=status_code, detail=detail)


def get_or_404(db: Session, model, id_value: int, detail: str = "No encontrado"):
    obj = db.query(model).filter(model.id == id_value).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj
