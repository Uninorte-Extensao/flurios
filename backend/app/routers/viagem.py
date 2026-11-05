from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.models.viagem import StatusViagem
from app.schemas.viagem import (
    LocalizacaoCreate,
    LocalizacaoOut,
    ViagemCreate,
    ViagemDetalheOut,
    ViagemEncomendaCreate,
    ViagemEncomendaOut,
    ViagemOut,
    ViagemStatusUpdate,
)
from app.services.encomenda import buscar_encomenda_por_id
from app.services.embarcacao import buscar_embarcacao_por_id
from app.schemas.embarcacao import EmbarcacaoOut
from app.schemas.encomenda import EncomendaOut
from app.schemas.parada import ParadaOut
from app.schemas.rota import RotaDetalheOut
from app.services.parada import buscar_parada_por_id, listar_paradas_da_rota
from app.services.rota import buscar_rota_por_id
from app.services.viagem import (
    associar_encomenda,
    atualizar_status_viagem,
    buscar_viagem_por_id,
    criar_viagem,
    listar_encomendas_da_viagem,
    listar_viagens,
    registrar_localizacao,
)

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


@router.patch("/{viagem_id}/status", response_model=ViagemOut)
def atualizar_status(
    viagem_id: int,
    dados: ViagemStatusUpdate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    viagem = buscar_viagem_por_id(db, viagem_id)

    if viagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem nao encontrada.",
        )

    try:
        return atualizar_status_viagem(db, viagem, dados.status)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))


@router.get("", response_model=list[ViagemOut])
def listar(
    status_viagem: StatusViagem | None = Query(default=None, alias="status"),
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    return listar_viagens(db, status_viagem)


@router.get("/{viagem_id}", response_model=ViagemDetalheOut)
def obter_viagem(
    viagem_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    viagem = buscar_viagem_por_id(db, viagem_id)

    if viagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem nao encontrada.",
        )

    rota = RotaDetalheOut.model_validate(buscar_rota_por_id(db, viagem.rota_id))
    rota.paradas = [
        ParadaOut.model_validate(p) for p in listar_paradas_da_rota(db, viagem.rota_id)
    ]

    return ViagemDetalheOut(
        **ViagemOut.model_validate(viagem).model_dump(),
        embarcacao=EmbarcacaoOut.model_validate(
            buscar_embarcacao_por_id(db, viagem.embarcacao_id)
        ),
        rota=rota,
    )


@router.get("/{viagem_id}/encomendas", response_model=list[EncomendaOut])
def listar_encomendas(
    viagem_id: int,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    if buscar_viagem_por_id(db, viagem_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem nao encontrada.",
        )

    return listar_encomendas_da_viagem(db, viagem_id)


@router.post(
    "/{viagem_id}/localizacao",
    response_model=LocalizacaoOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_localizacao_da_viagem(
    viagem_id: int,
    dados: LocalizacaoCreate,
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    viagem = buscar_viagem_por_id(db, viagem_id)

    if viagem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viagem nao encontrada.",
        )

    parada = buscar_parada_por_id(db, dados.parada_id)

    if parada is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parada nao encontrada.",
        )

    try:
        registradas = registrar_localizacao(db, viagem, parada)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))

    return LocalizacaoOut(
        viagem_id=viagem.id,
        parada_id=parada.id,
        encomendas_registradas=registradas,
    )
