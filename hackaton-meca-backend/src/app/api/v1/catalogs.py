from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.security import User
from app.crud import catalogs as crud_catalogs
from app.schemas.catalogs import (
    AreaOut,
    CuentaOut,
    FinanciadorOut,
    GestionOut,
    RegionOut,
    RubroOut,
    TipoCambioOut,
)

router = APIRouter()


@router.get("/regiones", response_model=List[RegionOut])
def list_regiones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_regiones(db)


@router.get("/areas", response_model=List[AreaOut])
def list_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_areas(db)


@router.get("/rubros", response_model=List[RubroOut])
def list_rubros(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_rubros_with_cuentas(db)


@router.get("/cuentas", response_model=List[CuentaOut])
def list_cuentas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_cuentas(db)


@router.get("/financiadores", response_model=List[FinanciadorOut])
def list_financiadores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_financiadores(db)


@router.get("/gestiones", response_model=List[GestionOut])
def list_gestiones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_gestiones(db)


@router.get("/tipos-cambio", response_model=List[TipoCambioOut])
def list_tipos_cambio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_catalogs.get_tipos_cambio(db)
