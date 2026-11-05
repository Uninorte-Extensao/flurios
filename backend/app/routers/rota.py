from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.schemas.parada import ParadaCreate, ParadaOut, ParadaUpdate
from app.schemas.rota import RotaCreate, RotaDetalheOut, RotaOut, RotaUpdate
from app.services.parada import (
    atualizar_parada,
    buscar_parada_da_rota,
    criar_parada,
    excluir_parada,
    listar_paradas_da_rota,
)
from app.services.rota import (
    atualizar_rota,
    buscar_rota_por_id,
    criar_rota,
    excluir_rota,
    listar_rotas,
)

router = APIRouter(prefix="/rotas", tags=["rotas"])


def _rota_ou_404(db: Session, rota_id: int):
    rota = buscar_rota_por_id(db, rota_id)

    if rota is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rota nao encontrada.",
        )

    return rota


def _parada_ou_404(db: Session, rota_id: int, parada_id: int):
    _rota_ou_404(db, rota_id)
    parada = buscar_parada_da_rota(db, rota_id, parada_id)

    if parada is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parada nao encontrada.",
        )

    return parada


@router.post("", response_model=RotaOut, status_code=status.HTTP_201_CREATED)
def cadastrar_rota(
    dados: RotaCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return criar_rota(db, dados)


@router.get("", response_model=list[RotaOut])
def listar(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return listar_rotas(db)


@router.get("/{rota_id}", response_model=RotaDetalheOut)
def obter_rota(
    rota_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    rota = _rota_ou_404(db, rota_id)
    resposta = RotaDetalheOut.model_validate(rota)
    resposta.paradas = [
        ParadaOut.model_validate(p) for p in listar_paradas_da_rota(db, rota.id)
    ]

    return resposta


@router.patch("/{rota_id}", response_model=RotaOut)
def editar_rota(
    rota_id: int,
    dados: RotaUpdate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return atualizar_rota(db, _rota_ou_404(db, rota_id), dados)


@router.delete("/{rota_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_rota(
    rota_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    try:
        excluir_rota(db, _rota_ou_404(db, rota_id))
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{rota_id}/paradas",
    response_model=ParadaOut,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_parada(
    rota_id: int,
    dados: ParadaCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    _rota_ou_404(db, rota_id)

    try:
        return criar_parada(db, rota_id, dados)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))


@router.get("/{rota_id}/paradas", response_model=list[ParadaOut])
def listar_paradas(
    rota_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    _rota_ou_404(db, rota_id)

    return listar_paradas_da_rota(db, rota_id)


@router.patch("/{rota_id}/paradas/{parada_id}", response_model=ParadaOut)
def editar_parada(
    rota_id: int,
    parada_id: int,
    dados: ParadaUpdate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    parada = _parada_ou_404(db, rota_id, parada_id)

    try:
        return atualizar_parada(db, parada, dados)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))


@router.delete(
    "/{rota_id}/paradas/{parada_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remover_parada(
    rota_id: int,
    parada_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    excluir_parada(db, _parada_ou_404(db, rota_id, parada_id))

    return Response(status_code=status.HTTP_204_NO_CONTENT)
