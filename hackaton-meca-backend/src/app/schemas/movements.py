from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MovimientoGastoOut(BaseModel):
    id: int
    fecha: str
    comprobante: str
    beneficiario: str
    concepto: str
    moneda: str
    tipoCambio: float
    montoBob: float
    montoUsd: float
    codigoCuenta: str
    nombreCuenta: str
    region: str
    area: str
    financiador: str
    loteImportacion: str
    auditHash: str

    model_config = ConfigDict(from_attributes=True)


class ImportacionLoteOut(BaseModel):
    id: int
    nombreArchivo: str
    fechaCarga: str
    usuarioCarga: str
    totalRegistros: int = 0
    totalMontoBob: float
    estado: str  # CONFIRMADO | REVERTIDO | EN_REVISION
    checksumSha256: str

    model_config = ConfigDict(from_attributes=True)
