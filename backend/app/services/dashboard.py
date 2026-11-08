from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.models.embarcacao import Embarcacao
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.parada import Parada
from app.models.rota import Rota
from app.models.viagem import StatusViagem, Viagem
from app.models.viagem_encomenda import ViagemEncomenda

# Encomenda que ainda ocupa espaco na embarcacao: nem entregue, nem em imprevisto.
STATUS_ENCOMENDA_FORA_DA_OCUPACAO = (StatusEncomenda.ENTREGUE, StatusEncomenda.IMPREVISTO)

# Rotulo do grupo de encomendas antigas, cadastradas antes de existir destino na encomenda.
MUNICIPIO_SEM_DESTINO = "Sem destino definido"


def contar_encomendas_por_status(db: Session) -> dict[str, int]:
    """Contagem de encomendas por status. Todos os status aparecem (zero se nao ha)."""
    linhas = (
        db.query(Encomenda.status, func.count(Encomenda.id))
        .group_by(Encomenda.status)
        .all()
    )
    contagem = {status.value: 0 for status in StatusEncomenda}

    for status, total in linhas:
        contagem[status.value] = total

    return contagem


def contar_viagens_por_status(db: Session) -> dict[str, int]:
    """Contagem de viagens por status. Todos os status aparecem (zero se nao ha)."""
    linhas = (
        db.query(Viagem.status, func.count(Viagem.id))
        .group_by(Viagem.status)
        .all()
    )
    contagem = {status.value: 0 for status in StatusViagem}

    for status, total in linhas:
        contagem[status.value] = total

    return contagem


def contar_encomendas_por_municipio(db: Session) -> list[tuple[str, int]]:
    """Encomendas por municipio de destino, do maior para o menor total.

    O destino e o da propria encomenda (parada_destino_id), nao o municipio do
    destinatario. Paradas de rotas diferentes com o mesmo nome contam juntas.
    Encomendas antigas, sem parada de destino, entram em um grupo proprio
    (MUNICIPIO_SEM_DESTINO), sempre por ultimo.
    """
    linhas = (
        db.query(Parada.nome, func.count(Encomenda.id))
        .select_from(Encomenda)
        .outerjoin(Parada, Parada.id == Encomenda.parada_destino_id)
        .group_by(Parada.nome)
        .all()
    )

    com_destino = sorted(
        ((nome, total) for nome, total in linhas if nome is not None),
        key=lambda linha: (-linha[1], linha[0]),
    )
    sem_destino = sum(total for nome, total in linhas if nome is None)

    if sem_destino:
        com_destino.append((MUNICIPIO_SEM_DESTINO, sem_destino))

    return com_destino


def calcular_ocupacao_viagens_em_andamento(db: Session) -> list[dict]:
    """Ocupacao de cada viagem em andamento.

    Convencao: a capacidade da embarcacao e um numero de encomendas. Ocupacao =
    encomendas ativas associadas a viagem / capacidade. "Ativa" = nao entregue e
    nao imprevisto.
    """
    ativas = func.count(Encomenda.id)
    linhas = (
        db.query(Viagem, Embarcacao, Rota.nome, ativas)
        .join(Embarcacao, Embarcacao.id == Viagem.embarcacao_id)
        .join(Rota, Rota.id == Viagem.rota_id)
        .outerjoin(ViagemEncomenda, ViagemEncomenda.viagem_id == Viagem.id)
        .outerjoin(
            Encomenda,
            (Encomenda.id == ViagemEncomenda.encomenda_id)
            & Encomenda.status.notin_(STATUS_ENCOMENDA_FORA_DA_OCUPACAO),
        )
        .filter(Viagem.status == StatusViagem.EM_ANDAMENTO)
        .group_by(Viagem.id, Embarcacao.id, Rota.nome)
        .order_by(Viagem.data_saida, Viagem.id)
        .all()
    )

    return [
        {
            "viagem_id": viagem.id,
            "embarcacao_id": embarcacao.id,
            "embarcacao_nome": embarcacao.nome,
            "rota_nome": rota_nome,
            "capacidade": embarcacao.capacidade,
            "encomendas_ativas": total,
            "ocupacao": round(total / embarcacao.capacidade, 4) if embarcacao.capacidade else 0.0,
        }
        for viagem, embarcacao, rota_nome, total in linhas
    ]


def listar_envios_ativos(db: Session) -> list[dict]:
    """Encomendas que ainda nao foram entregues, com a situacao na viagem.

    O municipio de destino e o da propria encomenda (parada_destino_id), nao o
    do destinatario; sem parada de destino, MUNICIPIO_SEM_DESTINO (mesmo
    rotulo do bloco de municipios).

    Viagem da encomenda = a mais recente que nao foi cancelada. Progresso =
    paradas da rota ja registradas na viagem / total de paradas da rota.
    Proxima parada = primeira parada (por ordem) ainda nao registrada. Sem
    viagem (ou sem paradas), progresso 0 e proxima parada nula.
    """
    encomendas = (
        db.query(Encomenda, Destinatario, Parada.nome)
        .join(Destinatario, Destinatario.id == Encomenda.destinatario_id)
        .outerjoin(Parada, Parada.id == Encomenda.parada_destino_id)
        .filter(Encomenda.status != StatusEncomenda.ENTREGUE)
        .order_by(Encomenda.id)
        .all()
    )
    if not encomendas:
        return []

    ids = [e.id for e, _, _ in encomendas]

    # viagem mais recente (nao cancelada) de cada encomenda
    viagem_da_encomenda: dict[int, Viagem] = {}
    vinculos = (
        db.query(ViagemEncomenda.encomenda_id, Viagem)
        .join(Viagem, Viagem.id == ViagemEncomenda.viagem_id)
        .filter(
            ViagemEncomenda.encomenda_id.in_(ids),
            Viagem.status != StatusViagem.CANCELADA,
        )
        .order_by(ViagemEncomenda.id)
        .all()
    )
    for encomenda_id, viagem in vinculos:
        viagem_da_encomenda[encomenda_id] = viagem

    viagem_ids = {v.id for v in viagem_da_encomenda.values()}
    rota_ids = {v.rota_id for v in viagem_da_encomenda.values()}

    paradas_por_rota: dict[int, list[Parada]] = {}
    if rota_ids:
        for parada in (
            db.query(Parada)
            .filter(Parada.rota_id.in_(rota_ids))
            .order_by(Parada.rota_id, Parada.ordem)
            .all()
        ):
            paradas_por_rota.setdefault(parada.rota_id, []).append(parada)

    registradas_por_viagem: dict[int, set[int]] = {}
    if viagem_ids:
        for viagem_id, parada_id in (
            db.query(Movimentacao.viagem_id, Movimentacao.parada_id)
            .filter(
                Movimentacao.viagem_id.in_(viagem_ids),
                Movimentacao.parada_id.isnot(None),
            )
            .distinct()
            .all()
        ):
            registradas_por_viagem.setdefault(viagem_id, set()).add(parada_id)

    envios = []
    for encomenda, destinatario, destino_nome in encomendas:
        proxima = None
        progresso = 0.0
        viagem = viagem_da_encomenda.get(encomenda.id)

        if viagem is not None:
            paradas = paradas_por_rota.get(viagem.rota_id, [])
            registradas = registradas_por_viagem.get(viagem.id, set())
            pendentes = [p for p in paradas if p.id not in registradas]

            if paradas:
                progresso = round((len(paradas) - len(pendentes)) / len(paradas), 4)
            if pendentes:
                proxima = pendentes[0].nome

        envios.append(
            {
                "codigo_rastreio": encomenda.codigo_rastreio,
                "destinatario": destinatario.nome,
                "municipio_destino": destino_nome or MUNICIPIO_SEM_DESTINO,
                "proxima_parada": proxima,
                "status": encomenda.status,
                "progresso": progresso,
            }
        )

    return envios


def listar_movimentacoes_recentes(db: Session, limite: int) -> list[dict]:
    """Ultimas movimentacoes (mais recente primeiro), de qualquer encomenda."""
    linhas = (
        db.query(Movimentacao, Encomenda.codigo_rastreio, Parada.nome)
        .join(Encomenda, Encomenda.id == Movimentacao.encomenda_id)
        .outerjoin(Parada, Parada.id == Movimentacao.parada_id)
        .order_by(Movimentacao.criado_em.desc(), Movimentacao.id.desc())
        .limit(limite)
        .all()
    )

    return [
        {
            "codigo_rastreio": codigo,
            "status": movimentacao.status,
            "parada": nome_parada,
            "data": movimentacao.criado_em,
        }
        for movimentacao, codigo, nome_parada in linhas
    ]
