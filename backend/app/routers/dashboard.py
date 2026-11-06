from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.dashboard import ResumoEncomendasOut
from app.services.dashboard import contar_encomendas_por_status

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumo", response_model=ResumoEncomendasOut)
def resumo(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    por_status = contar_encomendas_por_status(db)

    return ResumoEncomendasOut(total=sum(por_status.values()), por_status=por_status)
