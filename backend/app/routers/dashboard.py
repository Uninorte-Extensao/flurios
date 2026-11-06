from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import empresa_logado
from app.db.session import get_db
from app.models.empresa import Empresa
from app.models.viagem import StatusViagem
from app.schemas.dashboard import (
    EncomendasPorMunicipioOut,
    MunicipioContagemOut,
    OcupacaoOut,
    OcupacaoViagemOut,
    ResumoEncomendasOut,
    ResumoViagensOut,
)
from app.services.dashboard import (
    calcular_ocupacao_viagens_em_andamento,
    contar_encomendas_por_municipio,
    contar_encomendas_por_status,
    contar_viagens_por_status,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/resumo", response_model=ResumoEncomendasOut)
def resumo(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    por_status = contar_encomendas_por_status(db)

    return ResumoEncomendasOut(total=sum(por_status.values()), por_status=por_status)


@router.get("/viagens", response_model=ResumoViagensOut)
def resumo_viagens(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    por_status = contar_viagens_por_status(db)

    return ResumoViagensOut(
        em_andamento=por_status[StatusViagem.EM_ANDAMENTO.value],
        total=sum(por_status.values()),
        por_status=por_status,
    )


@router.get("/municipios", response_model=EncomendasPorMunicipioOut)
def encomendas_por_municipio(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    municipios = [
        MunicipioContagemOut(municipio=municipio, total=total)
        for municipio, total in contar_encomendas_por_municipio(db)
    ]

    return EncomendasPorMunicipioOut(
        total=sum(m.total for m in municipios),
        municipios=municipios,
    )


@router.get("/ocupacao", response_model=OcupacaoOut)
def ocupacao_das_viagens(
    empresa: Empresa = Depends(empresa_logado),
    db: Session = Depends(get_db),
):
    viagens = [
        OcupacaoViagemOut(**linha)
        for linha in calcular_ocupacao_viagens_em_andamento(db)
    ]

    return OcupacaoOut(total=len(viagens), viagens=viagens)
