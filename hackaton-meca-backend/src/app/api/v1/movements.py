from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.security import User
from app.crud import movements as crud_movements
from app.schemas.movements import ImportacionLoteOut, MovimientoGastoOut

router = APIRouter()


@router.get(
    "",
    response_model=List[MovimientoGastoOut],
    dependencies=[Depends(require_permission("reportes.ver"))],
)
def list_movements(
    gestion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_movements.list_movimientos(db, gestion_id)


@router.get(
    "/batches",
    response_model=List[ImportacionLoteOut],
    dependencies=[Depends(require_permission("importaciones.ver"))],
)
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return crud_movements.list_batches(db)


@router.post(
    "/import-excel",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("importaciones.crear"))],
)
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Se requiere un archivo Excel (.xlsx)",
        )

    content = await file.read()
    try:
        res = crud_movements.import_excel_file(
            db=db,
            file_bytes=content,
            filename=file.filename,
            user_id=current_user.id,
        )
        return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error procesando archivo Excel: {str(exc)}",
        )


@router.delete(
    "/batches/{batch_id}",
    dependencies=[Depends(require_permission("importaciones.revertir"))],
)
def revert_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    success = crud_movements.revert_batch(db, batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lote de importación no encontrado")
    return {"message": f"Lote #{batch_id} revertido exitosamente"}
