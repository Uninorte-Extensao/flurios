from sqlalchemy.orm import Session

from app.core.rastreio import gerar_codigo_rastreio
from app.models.cliente import Cliente
from app.models.destinatario import Destinatario
from app.models.encomenda import Encomenda, StatusEncomenda
from app.schemas.encomenda import EncomendaCreate

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
        descricao=dados.descricao,
        codigo_rastreio=gerar_codigo_rastreio_unico(db),
        status=StatusEncomenda.PENDENTE,
    )

    db.add(nova_encomenda)
    db.commit()
    db.refresh(nova_encomenda)

    return nova_encomenda
