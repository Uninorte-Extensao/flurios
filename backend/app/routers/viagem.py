from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.viagem import ViagemCreate, ViagemOut
from app.services.embarcacao import buscar_embarcacao_por_id
from app.services.rota import buscar_rota_por_id
from app.services.viagem import criar_viagem

router = APIRouter(prefix="/viagens", tags=["viagens"])


@router.post("", response_model=ViagemOut, status_code=status.HTTP_201_CREATED)
def cadastrar_viagem(
    dados: ViagemCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    if buscar_embarcacao_por_id(db, dados.embarcacao_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Embarcacao nao encontrada.",
        )

    if buscar_rota_por_id(db, dados.rota_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rota nao encontrada.",
        )

    return criar_viagem(db, dados)
