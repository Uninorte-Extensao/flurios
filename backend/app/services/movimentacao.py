from sqlalchemy.orm import Session

from app.models.encomenda import StatusEncomenda
from app.models.movimentacao import Movimentacao
from app.models.parada import Parada
from app.schemas.movimentacao import MovimentacaoOut


def registrar_movimentacao(
    db: Session,
    encomenda_id: int,
    status: StatusEncomenda,
    viagem_id: int | None = None,
    parada_id: int | None = None,
) -> Movimentacao:
    """Adiciona uma movimentacao a sessao, sem commit.

    Quem chama e responsavel pelo commit, para que a movimentacao seja
    gravada na mesma transacao da mudanca que a originou.
    """
    movimentacao = Movimentacao(
        encomenda_id=encomenda_id,
        status=status,
        viagem_id=viagem_id,
        parada_id=parada_id,
    )

    db.add(movimentacao)

    return movimentacao


def listar_historico_da_encomenda(db: Session, encomenda_id: int) -> list[MovimentacaoOut]:
    """Historico completo da encomenda, do mais antigo para o mais recente."""
    linhas = (
        db.query(Movimentacao, Parada.nome)
        .outerjoin(Parada, Parada.id == Movimentacao.parada_id)
        .filter(Movimentacao.encomenda_id == encomenda_id)
        .order_by(Movimentacao.criado_em, Movimentacao.id)
        .all()
    )

    return [
        MovimentacaoOut(
            id=m.id,
            status=m.status,
            parada_id=m.parada_id,
            parada_nome=nome_parada,
            viagem_id=m.viagem_id,
            criado_em=m.criado_em,
        )
        for m, nome_parada in linhas
    ]
