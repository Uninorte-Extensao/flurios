from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.embarcacao import EmbarcacaoCreate, EmbarcacaoOut, EmbarcacaoUpdate
from app.services.embarcacao import (
    atualizar_embarcacao,
    buscar_embarcacao_por_id,
    criar_embarcacao,
    excluir_embarcacao,
    listar_embarcacoes,
)

router = APIRouter(prefix="/embarcacoes", tags=["embarcacoes"])


def _embarcacao_ou_404(db: Session, embarcacao_id: int):
    embarcacao = buscar_embarcacao_por_id(db, embarcacao_id)

    if embarcacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Embarcacao nao encontrada.",
        )

    return embarcacao


@router.post("", response_model=EmbarcacaoOut, status_code=status.HTTP_201_CREATED)
def cadastrar_embarcacao(
    dados: EmbarcacaoCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return criar_embarcacao(db, dados)


@router.get("", response_model=list[EmbarcacaoOut])
def listar(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return listar_embarcacoes(db)


@router.get("/{embarcacao_id}", response_model=EmbarcacaoOut)
def obter_embarcacao(
    embarcacao_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return _embarcacao_ou_404(db, embarcacao_id)


@router.patch("/{embarcacao_id}", response_model=EmbarcacaoOut)
def editar_embarcacao(
    embarcacao_id: int,
    dados: EmbarcacaoUpdate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    embarcacao = _embarcacao_ou_404(db, embarcacao_id)

    return atualizar_embarcacao(db, embarcacao, dados)


@router.delete("/{embarcacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_embarcacao(
    embarcacao_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    embarcacao = _embarcacao_ou_404(db, embarcacao_id)

    try:
        excluir_embarcacao(db, embarcacao)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
