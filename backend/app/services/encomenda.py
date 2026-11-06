from sqlalchemy.orm import Session

from app.core.rastreio import gerar_codigo_rastreio
from app.models.cliente import Cliente
from app.models.destinatario import Destinatario
from app.models.encomenda import Encomenda, StatusEncomenda
from app.schemas.encomenda import EncomendaCreate
from app.services.movimentacao import registrar_movimentacao

MAX_TENTATIVAS_CODIGO = 10


def gerar_codigo_rastreio_unico(db: Session) -> str:
    for _ in range(MAX_TENTATIVAS_CODIGO):
        codigo = gerar_codigo_rastreio()

        existe = (
            db.query(Encomenda)
            .filter(Encomenda.codigo_rastreio == codigo)
            .first()
        )

        if not existe:
            return codigo

    raise RuntimeError("Nao foi possivel gerar um codigo de rastreio unico.")


def buscar_encomenda_do_cliente(
    db: Session,
    codigo_rastreio: str,
    cliente_id: int,
) -> Encomenda | None:
    return (
        db.query(Encomenda)
        .filter(
            Encomenda.codigo_rastreio == codigo_rastreio,
            Encomenda.cliente_id == cliente_id,
        )
        .first()
    )


def buscar_encomenda_por_codigo(db: Session, codigo_rastreio: str) -> Encomenda | None:
    return (
        db.query(Encomenda)
        .filter(Encomenda.codigo_rastreio == codigo_rastreio)
        .first()
    )


def buscar_encomenda_por_id(db: Session, encomenda_id: int) -> Encomenda | None:
    return db.query(Encomenda).filter(Encomenda.id == encomenda_id).first()


def atualizar_status_encomenda(
    db: Session,
    encomenda: Encomenda,
    novo_status: StatusEncomenda,
    commit: bool = True,
    viagem_id: int | None = None,
    parada_id: int | None = None,
) -> Encomenda:
    """Muda o status e registra a movimentacao correspondente.

    Status e movimentacao sao gravados no mesmo commit. Se o status nao
    mudou, nada e registrado. Com commit=False, quem chama fecha a transacao.
    """
    if encomenda.status != novo_status:
        encomenda.status = novo_status
        registrar_movimentacao(
            db,
            encomenda.id,
            novo_status,
            viagem_id=viagem_id,
            parada_id=parada_id,
        )

    if commit:
        db.commit()
        db.refresh(encomenda)

    return encomenda


def listar_encomendas_do_cliente(db: Session, cliente_id: int) -> list[Encomenda]:
    return (
        db.query(Encomenda)
        .filter(Encomenda.cliente_id == cliente_id)
        .order_by(Encomenda.criado_em.desc())
        .all()
    )


def criar_encomenda(
    db: Session,
    cliente: Cliente,
    destinatario: Destinatario,
    dados: EncomendaCreate,
) -> Encomenda:
    nova_encomenda = Encomenda(
        cliente_id=cliente.id,
        destinatario_id=destinatario.id,
        parada_destino_id=dados.parada_destino_id,
        descricao=dados.descricao,
        codigo_rastreio=gerar_codigo_rastreio_unico(db),
        status=StatusEncomenda.PENDENTE,
    )

    db.add(nova_encomenda)
    db.flush()
    registrar_movimentacao(db, nova_encomenda.id, nova_encomenda.status)
    db.commit()
    db.refresh(nova_encomenda)

    return nova_encomenda
