from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.viagem import (
    ViagemCreate,
    ViagemEncomendaCreate,
    ViagemEncomendaOut,
    ViagemOut,
)
from app.services.encomenda import buscar_encomenda_por_id
from app.services.embarcacao import buscar_embarcacao_por_id
from app.services.rota import buscar_rota_por_id
from app.services.viagem import associar_encomenda, buscar_viagem_por_id, criar_viagem

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


@router.post(
    "/{viagem_id}/encomendas",
    response_model=ViagemEncomendaOut,
    status_code=status.HTTP_201_CREATED,
)
def associar_encomenda_a_viagem(
    viagem_id: int,
    dados: ViagemEncomendaCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    viagem = buscar_viagem_por_id(db, viagem_id)

    if viagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem nao encontrada.",
        )

    encomenda = buscar_encomenda_por_id(db, dados.encomenda_id)

    if encomenda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Encomenda nao encontrada.",
        )

    try:
        return associar_encomenda(db, viagem, encomenda)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
