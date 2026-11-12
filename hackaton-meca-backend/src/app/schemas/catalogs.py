from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RegionOut(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class AreaOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CuentaOut(BaseModel):
    id: int
    rubro_id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RubroOut(BaseModel):
    id: int
    code: str
    name: str
    cuentas: List[CuentaOut] = []

    model_config = ConfigDict(from_attributes=True)


class FinanciadorOut(BaseModel):
    id: int
    grupo_id: Optional[int] = None
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    moneda: str

    model_config = ConfigDict(from_attributes=True)


class GestionOut(BaseModel):
    id: int
    year: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TipoCambioOut(BaseModel):
    id: int
    fecha: date
    tipo: str
    rate: float

    model_config = ConfigDict(from_attributes=True)
