from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models.catalogs import (
    Area,
    Cuenta,
    Financiador,
    Gestion,
    Region,
    Rubro,
    TipoCambio,
)


def get_regiones(db: Session):
    return db.scalars(select(Region).order_by(Region.code)).all()


def get_areas(db: Session):
    return db.scalars(select(Area).order_by(Area.name)).all()


def get_rubros_with_cuentas(db: Session):
    return db.scalars(select(Rubro).options(selectinload(Rubro.cuentas)).order_by(Rubro.code)).all()


def get_cuentas(db: Session):
    return db.scalars(select(Cuenta).order_by(Cuenta.code)).all()


def get_financiadores(db: Session):
    return db.scalars(select(Financiador).order_by(Financiador.name)).all()


def get_gestiones(db: Session):
    return db.scalars(select(Gestion).order_by(Gestion.year.desc())).all()


def get_tipos_cambio(db: Session):
    return db.scalars(select(TipoCambio).order_by(TipoCambio.fecha.desc())).all()
