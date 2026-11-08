from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.embarcacao import Embarcacao
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import STATUS_VIAGEM_ATIVOS, StatusViagem, Viagem
from app.models.viagem_encomenda import ViagemEncomenda
from app.schemas.viagem import ViagemCreate
from app.services.dashboard import STATUS_ENCOMENDA_FORA_DA_OCUPACAO
from app.services.encomenda import atualizar_status_encomenda
from app.services.movimentacao import registrar_movimentacao

# Fluxo linear: concluida e cancelada sao estados finais.
TRANSICOES_VIAGEM = {
    StatusViagem.PROGRAMADA: {StatusViagem.EM_ANDAMENTO, StatusViagem.CANCELADA},
    StatusViagem.EM_ANDAMENTO: {StatusViagem.CONCLUIDA, StatusViagem.CANCELADA},
    StatusViagem.CONCLUIDA: set(),
    StatusViagem.CANCELADA: set(),
}

MENSAGEM_VIAGEM_NAO_EM_ANDAMENTO = (
    "So e possivel registrar localizacao em viagem em andamento."
)
MENSAGEM_PARADA_FORA_DA_ROTA = "A parada nao pertence a rota da viagem."

MENSAGEM_VIAGEM_NAO_ATIVA = (
    "So e possivel associar encomendas a viagens programadas ou em andamento."
)
MENSAGEM_ENCOMENDA_JA_ASSOCIADA = (
    "Encomenda ja esta associada a uma viagem ativa."
)
MENSAGEM_STATUS_ENCOMENDA_INVALIDO = (
    "So e possivel associar encomendas com status recebida ou aguardando_embarque."
)
MENSAGEM_ENCOMENDA_SEM_DESTINO = "A encomenda nao tem destino definido."
MENSAGEM_DESTINO_FORA_DA_ROTA = "O destino da encomenda nao pertence a rota da viagem."
MENSAGEM_EMBARCACAO_SEM_CAPACIDADE = (
    "A embarcacao da viagem nao tem capacidade para mais encomendas."
)
MENSAGEM_EMBARCACAO_INATIVA = "Nao e possivel programar viagem com embarcacao inativa."
MENSAGEM_ROTA_SEM_PARADAS = "Nao e possivel programar viagem com rota sem paradas."
MENSAGEM_REMOCAO_SO_PROGRAMADA = (
    "So e possivel remover encomendas de viagens programadas."
)
MENSAGEM_ENCOMENDA_NAO_ESTA_NA_VIAGEM = "A encomenda nao esta associada a esta viagem."

# Unicos status em que a encomenda esta pronta para ser colocada em uma viagem.
STATUS_ENCOMENDA_ASSOCIAVEIS = (
    StatusEncomenda.RECEBIDA,
    StatusEncomenda.AGUARDANDO_EMBARQUE,
)


def validar_programacao(db: Session, embarcacao: Embarcacao, rota: Rota) -> None:
    """Recusa viagem com embarcacao inativa ou rota sem paradas."""
    if not embarcacao.ativa:
        raise ValueError(MENSAGEM_EMBARCACAO_INATIVA)

    tem_paradas = db.query(Parada.id).filter(Parada.rota_id == rota.id).first()

    if tem_paradas is None:
        raise ValueError(MENSAGEM_ROTA_SEM_PARADAS)


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


def contar_encomendas_ativas_da_viagem(db: Session, viagem_id: int) -> int:
    """Encomendas associadas que ainda ocupam espaco (nem entregues, nem em imprevisto).

    Mesma convencao da ocupacao do dashboard.
    """
    return (
        db.query(func.count(Encomenda.id))
        .join(ViagemEncomenda, ViagemEncomenda.encomenda_id == Encomenda.id)
        .filter(
            ViagemEncomenda.viagem_id == viagem_id,
            Encomenda.status.notin_(STATUS_ENCOMENDA_FORA_DA_OCUPACAO),
        )
        .scalar()
    )


def associar_encomenda(
    db: Session,
    viagem: Viagem,
    encomenda: Encomenda,
) -> ViagemEncomenda:
    """Coloca a encomenda na viagem e a passa para aguardando_embarque.

    ValueError: viagem inativa, encomenda ja em viagem ativa, status invalido,
    sem destino, destino fora da rota ou embarcacao sem capacidade.
    """
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

    if encomenda.status not in STATUS_ENCOMENDA_ASSOCIAVEIS:
        raise ValueError(MENSAGEM_STATUS_ENCOMENDA_INVALIDO)

    if encomenda.parada_destino_id is None:
        raise ValueError(MENSAGEM_ENCOMENDA_SEM_DESTINO)

    destino_na_rota = (
        db.query(Parada.id)
        .filter(
            Parada.id == encomenda.parada_destino_id,
            Parada.rota_id == viagem.rota_id,
        )
        .first()
    )

    if destino_na_rota is None:
        raise ValueError(MENSAGEM_DESTINO_FORA_DA_ROTA)

    embarcacao = db.get(Embarcacao, viagem.embarcacao_id)

    if contar_encomendas_ativas_da_viagem(db, viagem.id) >= embarcacao.capacidade:
        raise ValueError(MENSAGEM_EMBARCACAO_SEM_CAPACIDADE)

    vinculo = ViagemEncomenda(viagem_id=viagem.id, encomenda_id=encomenda.id)

    db.add(vinculo)
    # Vinculo, status e movimentacao (com a viagem) saem no mesmo commit. Se a
    # encomenda ja estava aguardando embarque, nada e registrado de novo.
    atualizar_status_encomenda(
        db,
        encomenda,
        StatusEncomenda.AGUARDANDO_EMBARQUE,
        commit=False,
        viagem_id=viagem.id,
    )
    db.commit()
    db.refresh(vinculo)

    return vinculo


def remover_encomenda(db: Session, viagem: Viagem, encomenda: Encomenda) -> None:
    """Tira a encomenda de uma viagem programada e a devolve ao status recebida.

    Status e movimentacao (com a viagem de origem) saem no mesmo commit do
    desfazimento do vinculo. Se a encomenda ja estava recebida, o status nao
    muda e nenhuma movimentacao repetida e gravada. ValueError: viagem fora de
    programada. LookupError: a encomenda nao esta nessa viagem.
    """
    if viagem.status != StatusViagem.PROGRAMADA:
        raise ValueError(MENSAGEM_REMOCAO_SO_PROGRAMADA)

    vinculo = (
        db.query(ViagemEncomenda)
        .filter(
            ViagemEncomenda.viagem_id == viagem.id,
            ViagemEncomenda.encomenda_id == encomenda.id,
        )
        .first()
    )

    if vinculo is None:
        raise LookupError(MENSAGEM_ENCOMENDA_NAO_ESTA_NA_VIAGEM)

    db.delete(vinculo)
    atualizar_status_encomenda(
        db,
        encomenda,
        StatusEncomenda.RECEBIDA,
        commit=False,
        viagem_id=viagem.id,
    )
    db.commit()


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

    if novo_status == StatusViagem.CANCELADA:
        marcar_encomendas_como_imprevisto(db, viagem)

    db.commit()
    db.refresh(viagem)

    return viagem


def marcar_encomendas_como_imprevisto(db: Session, viagem: Viagem) -> None:
    """Passa para imprevisto as encomendas da viagem cancelada.

    Encomendas ja entregues nao sao alteradas. Nao faz commit: roda na mesma
    transacao do cancelamento, para que viagem e encomendas mudem juntas.
    """
    encomendas = (
        db.query(Encomenda)
        .join(ViagemEncomenda, ViagemEncomenda.encomenda_id == Encomenda.id)
        .filter(
            ViagemEncomenda.viagem_id == viagem.id,
            Encomenda.status.notin_(
                [StatusEncomenda.ENTREGUE, StatusEncomenda.IMPREVISTO]
            ),
        )
        .all()
    )

    for encomenda in encomendas:
        atualizar_status_encomenda(
            db,
            encomenda,
            StatusEncomenda.IMPREVISTO,
            commit=False,
            viagem_id=viagem.id,
        )


def listar_viagens(
    db: Session,
    status: StatusViagem | None = None,
) -> list[Viagem]:
    consulta = db.query(Viagem)

    if status is not None:
        consulta = consulta.filter(Viagem.status == status)

    return consulta.order_by(Viagem.data_saida.desc(), Viagem.id.desc()).all()


def listar_encomendas_da_viagem(db: Session, viagem_id: int) -> list[Encomenda]:
    return (
        db.query(Encomenda)
        .join(ViagemEncomenda, ViagemEncomenda.encomenda_id == Encomenda.id)
        .filter(ViagemEncomenda.viagem_id == viagem_id)
        .order_by(ViagemEncomenda.id)
        .all()
    )


def registrar_localizacao(db: Session, viagem: Viagem, parada: Parada) -> int:
    """Registra que a viagem chegou a uma parada da sua rota.

    Para cada encomenda da viagem que esta a bordo (embarcada ou em_transito)
    grava uma movimentacao com a parada e a viagem. Encomendas embarcadas
    passam a em_transito. Tudo no mesmo commit. Retorna quantas encomendas
    receberam o registro.
    """
    if viagem.status != StatusViagem.EM_ANDAMENTO:
        raise ValueError(MENSAGEM_VIAGEM_NAO_EM_ANDAMENTO)

    if parada.rota_id != viagem.rota_id:
        raise ValueError(MENSAGEM_PARADA_FORA_DA_ROTA)

    a_bordo = (
        db.query(Encomenda)
        .join(ViagemEncomenda, ViagemEncomenda.encomenda_id == Encomenda.id)
        .filter(
            ViagemEncomenda.viagem_id == viagem.id,
            Encomenda.status.in_(
                [StatusEncomenda.EMBARCADA, StatusEncomenda.EM_TRANSITO]
            ),
        )
        .order_by(Encomenda.id)
        .all()
    )

    for encomenda in a_bordo:
        if encomenda.status == StatusEncomenda.EMBARCADA:
            atualizar_status_encomenda(
                db,
                encomenda,
                StatusEncomenda.EM_TRANSITO,
                commit=False,
                viagem_id=viagem.id,
                parada_id=parada.id,
            )
        else:
            registrar_movimentacao(
                db,
                encomenda.id,
                encomenda.status,
                viagem_id=viagem.id,
                parada_id=parada.id,
            )

    db.commit()

    return len(a_bordo)
