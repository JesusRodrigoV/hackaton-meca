import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def handle_integrity_error(
    detail: str = "Conflicto de datos",
    status_code: int = status.HTTP_409_CONFLICT,
):
    logger.exception("IntegrityError: %s", detail)
    raise HTTPException(status_code=status_code, detail=detail)


def get_or_404(db: Session, model, id_value, detail: str = "No encontrado"):
    obj = db.query(model).filter(model.id == id_value).first()
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return obj