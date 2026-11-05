from sqlalchemy.orm import Session

from app.models.encomenda import Encomenda
from app.models.viagem import STATUS_VIAGEM_ATIVOS, StatusViagem, Viagem
from app.models.viagem_encomenda import ViagemEncomenda
from app.schemas.viagem import ViagemCreate

# Fluxo linear: concluida e cancelada sao estados finais.
TRANSICOES_VIAGEM = {
    StatusViagem.PROGRAMADA: {StatusViagem.EM_ANDAMENTO, StatusViagem.CANCELADA},
    StatusViagem.EM_ANDAMENTO: {StatusViagem.CONCLUIDA, StatusViagem.CANCELADA},
    StatusViagem.CONCLUIDA: set(),
    StatusViagem.CANCELADA: set(),
}

MENSAGEM_VIAGEM_NAO_ATIVA = (
    "So e possivel associar encomendas a viagens programadas ou em andamento."
)
MENSAGEM_ENCOMENDA_JA_ASSOCIADA = (
    "Encomenda ja esta associada a uma viagem ativa."
)


def criar_viagem(db: Session, dados: ViagemCreate) -> Viagem:
    nova_viagem = Viagem(
        embarcacao_id=dados.embarcacao_id,
        rota_id=dados.rota_id,
        data_saida=dados.data_saida,
        status=StatusViagem.PROGRAMADA,
    )

    db.add(nova_viagem)
    db.commit()
    db.refresh(nova_viagem)

    return nova_viagem


def buscar_viagem_por_id(db: Session, viagem_id: int) -> Viagem | None:
    return db.query(Viagem).filter(Viagem.id == viagem_id).first()


def associar_encomenda(
    db: Session,
    viagem: Viagem,
    encomenda: Encomenda,
) -> ViagemEncomenda:
    if viagem.status not in STATUS_VIAGEM_ATIVOS:
        raise ValueError(MENSAGEM_VIAGEM_NAO_ATIVA)

    ja_em_viagem_ativa = (
        db.query(ViagemEncomenda.id)
        .join(Viagem, Viagem.id == ViagemEncomenda.viagem_id)
        .filter(
            ViagemEncomenda.encomenda_id == encomenda.id,
            Viagem.status.in_(STATUS_VIAGEM_ATIVOS),
        )
        .first()
    )

    if ja_em_viagem_ativa is not None:
        raise ValueError(MENSAGEM_ENCOMENDA_JA_ASSOCIADA)

    vinculo = ViagemEncomenda(viagem_id=viagem.id, encomenda_id=encomenda.id)

    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)

    return vinculo


def atualizar_status_viagem(
    db: Session,
    viagem: Viagem,
    novo_status: StatusViagem,
) -> Viagem:
    if novo_status not in TRANSICOES_VIAGEM[viagem.status]:
        raise ValueError(
            f"Transicao de status invalida: {viagem.status.value} -> {novo_status.value}."
        )

    viagem.status = novo_status

    db.commit()
    db.refresh(viagem)

    return viagem
