from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PresupuestoTechoOut(BaseModel):
    id: int
    codigoCuenta: str
    nombreCuenta: str
    rubro: str
    region: str
    area: str
    financiador: str
    montoInicialBob: float
    modificacionesBob: float
    montoVigenteBob: float
    montoEjecutadoBob: float
    saldoDisponibleBob: float
    porcentajeEjecucion: float
    estado: str  # OK | SOBREEJECUCION | SIN_EJECUCION | EJECUCION_SIN_PRESUPUESTO

    model_config = ConfigDict(from_attributes=True)


class PresupuestoCreate(BaseModel):
    gestion_id: int
    region_id: int
    area_id: int
    financiador_id: int
    rubro_id: int
    cuenta_id: Optional[int] = None
    month: Optional[int] = None
    monto_bob: float = Field(..., gt=0)
    linea: Optional[str] = None


class ModificacionCreate(BaseModel):
    financiadorOrigen: str
    financiadorDestino: str
    partida: str
    montoBob: float = Field(..., gt=0)
    motivo: str


class ModificacionApproveRequest(BaseModel):
    aprobador: Optional[str] = "Administrador"


class ModificacionPresupuestariaOut(BaseModel):
    id: int
    fecha: str
    financiadorOrigen: str
    financiadorDestino: str
    partida: str
    montoBob: float
    motivo: str
    solicitante: str
    aprobador: Optional[str] = None
    estado: str  # PENDIENTE | APROBADO | RECHAZADO

    model_config = ConfigDict(from_attributes=True)
