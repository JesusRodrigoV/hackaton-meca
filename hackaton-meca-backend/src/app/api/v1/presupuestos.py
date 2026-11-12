from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.security import User
from app.crud import presupuestos as crud_presupuestos
from app.schemas.presupuestos import (
    ModificacionApproveRequest,
    ModificacionCreate,
    ModificacionPresupuestariaOut,
    PresupuestoCreate,
    PresupuestoTechoOut,
)

router = APIRouter()


@router.get(
    "/techos",
    response_model=List[PresupuestoTechoOut],
    dependencies=[Depends(require_permission("presupuestos.ver"))],
)
def get_techos(
    gestion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_presupuestos.get_techos_presupuestarios(db, gestion_id)


@router.post(
    "/techos",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("presupuestos.editar"))],
)
def create_techo(
    payload: PresupuestoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    p = crud_presupuestos.create_presupuesto(db, payload)
    return {"id": p.id, "message": "Techo presupuestario creado correctamente"}


@router.get(
    "/modificaciones",
    response_model=List[ModificacionPresupuestariaOut],
    dependencies=[Depends(require_permission("presupuestos.ver"))],
)
def get_modificaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items = crud_presupuestos.list_modificaciones(db)
    output = []
    for m in items:
        # Extraer nombres descriptivos
        fin_orig = m.origen_presupuesto.financiador.name if m.origen_presupuesto else "Sin Asignar"
        fin_dest = m.destino_presupuesto.financiador.name if m.destino_presupuesto else "Sin Asignar"
        partida = m.reason.split("]")[0].replace("[", "") if "]" in m.reason else "Partida General"
        motivo = m.reason.split("]")[-1].strip() if "]" in m.reason else m.reason

        estado_map = {
            "borrador": "PENDIENTE",
            "aprobado": "APROBADO",
            "rechazado": "RECHAZADO",
        }

        output.append(
            ModificacionPresupuestariaOut(
                id=m.id,
                fecha=m.created_at.strftime("%Y-%m-%d") if m.created_at else "",
                financiadorOrigen=fin_orig,
                financiadorDestino=fin_dest,
                partida=partida,
                montoBob=float(m.amount_bob),
                motivo=motivo,
                solicitante="Coordinador de Proyecto",
                aprobador="Administrador" if m.estado == "aprobado" else None,
                estado=estado_map.get(m.estado, "PENDIENTE"),
            )
        )
    return output


@router.post(
    "/modificaciones",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("modificaciones.solicitar"))],
)
def create_modificacion(
    payload: ModificacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    mod = crud_presupuestos.create_modificacion(
        db, payload, user_id=current_user.id, user_email=current_user.email
    )
    return {
        "id": mod.id,
        "message": "Solicitud de modificación presupuestaria registrada",
        "estado": "PENDIENTE",
    }


@router.put(
    "/modificaciones/{mod_id}/aprobar",
    dependencies=[Depends(require_permission("modificaciones.aprobar"))],
)
def approve_modificacion(
    mod_id: int,
    payload: Optional[ModificacionApproveRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    aprobador = payload.aprobador if payload and payload.aprobador else current_user.full_name
    mod = crud_presupuestos.approve_modificacion(
        db, mod_id=mod_id, user_id=current_user.id, aprobador_name=aprobador
    )
    if not mod:
        raise HTTPException(status_code=404, detail="Modificación no encontrada")
    return {"id": mod.id, "message": "Modificación presupuestaria aprobada", "estado": "APROBADO"}


@router.put(
    "/modificaciones/{mod_id}/rechazar",
    dependencies=[Depends(require_permission("modificaciones.aprobar"))],
)
def reject_modificacion(
    mod_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    mod = crud_presupuestos.reject_modificacion(db, mod_id=mod_id, user_id=current_user.id)
    if not mod:
        raise HTTPException(status_code=404, detail="Modificación no encontrada")
    return {"id": mod.id, "message": "Modificación presupuestaria rechazada", "estado": "RECHAZADO"}
