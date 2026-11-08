from sqlalchemy import exists
from sqlalchemy.orm import Session

from app.core.rastreio import gerar_codigo_rastreio
from app.models.cliente import Cliente
from app.models.destinatario import Destinatario
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.parada import Parada
from app.models.viagem import STATUS_VIAGEM_ATIVOS, Viagem
from app.models.viagem_encomenda import ViagemEncomenda
from app.schemas.encomenda import (
    DestinatarioResumoOut,
    EncomendaCreate,
    EncomendaEmpresaOut,
    ViagemAtivaResumoOut,
)
from app.services.movimentacao import registrar_movimentacao

MAX_TENTATIVAS_CODIGO = 10

# Mudancas de status permitidas pelo PATCH /encomendas/{id}/status (manual). "entregue" nao
# aparece: so a retirada o gera. Os fluxos que mudam o status por dentro (associar, remover da
# viagem, cancelar viagem, localizacao, retirada) chamam atualizar_status_encomenda direto e
# nao passam por esta tabela.
TRANSICOES_MANUAIS: dict[StatusEncomenda, frozenset[StatusEncomenda]] = {
    StatusEncomenda.PENDENTE: frozenset(
        {StatusEncomenda.RECEBIDA, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.RECEBIDA: frozenset(
        {StatusEncomenda.AGUARDANDO_EMBARQUE, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.AGUARDANDO_EMBARQUE: frozenset(
        {StatusEncomenda.EMBARCADA, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.EMBARCADA: frozenset(
        {StatusEncomenda.EM_TRANSITO, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.EM_TRANSITO: frozenset(
        {StatusEncomenda.CHEGOU_AO_DESTINO, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.CHEGOU_AO_DESTINO: frozenset(
        {StatusEncomenda.A_RETIRAR, StatusEncomenda.IMPREVISTO}
    ),
    StatusEncomenda.A_RETIRAR: frozenset({StatusEncomenda.IMPREVISTO}),
    StatusEncomenda.ENTREGUE: frozenset(),
    StatusEncomenda.IMPREVISTO: frozenset({StatusEncomenda.RECEBIDA}),
}


def transicao_manual_valida(atual: StatusEncomenda, novo: StatusEncomenda) -> bool:
    return novo in TRANSICOES_MANUAIS.get(atual, frozenset())


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


def _encomenda_tem_viagem_ativa():
    return exists().where(
        ViagemEncomenda.encomenda_id == Encomenda.id,
        ViagemEncomenda.viagem_id == Viagem.id,
        Viagem.status.in_(STATUS_VIAGEM_ATIVOS),
    )


def listar_encomendas_da_empresa(
    db: Session,
    status: list[StatusEncomenda] | None = None,
    parada_destino_id: int | None = None,
    rota_id: int | None = None,
    sem_viagem_ativa: bool = False,
    busca: str | None = None,
    limite: int = 20,
    deslocamento: int = 0,
) -> tuple[list[EncomendaEmpresaOut], int]:
    """Lista encomendas de todos os clientes, com filtros opcionais combinados (E).

    Retorna a pagina pedida e o total antes da paginacao. O CPF do destinatario
    sai mascarado pelo schema de saida.
    """
    consulta = db.query(Encomenda)

    if status:
        consulta = consulta.filter(Encomenda.status.in_(status))

    if parada_destino_id is not None:
        consulta = consulta.filter(Encomenda.parada_destino_id == parada_destino_id)

    if rota_id is not None:
        consulta = consulta.filter(
            Encomenda.parada_destino_id.in_(
                db.query(Parada.id).filter(Parada.rota_id == rota_id)
            )
        )

    if sem_viagem_ativa:
        consulta = consulta.filter(~_encomenda_tem_viagem_ativa())

    if busca:
        consulta = consulta.filter(
            Encomenda.codigo_rastreio.icontains(busca.strip(), autoescape=True)
        )

    total = consulta.count()
    encomendas = (
        consulta.order_by(Encomenda.criado_em.desc(), Encomenda.id.desc())
        .limit(limite)
        .offset(deslocamento)
        .all()
    )

    viagens_ativas = _viagens_ativas_por_encomenda(db, [e.id for e in encomendas])

    itens = [
        EncomendaEmpresaOut(
            id=e.id,
            codigo_rastreio=e.codigo_rastreio,
            status=e.status,
            descricao=e.descricao,
            destinatario=DestinatarioResumoOut(
                nome=e.destinatario.nome, cpf=e.destinatario.cpf
            ),
            parada_destino_id=e.parada_destino_id,
            destino_nome=e.destino_nome,
            criado_em=e.criado_em,
            viagem_ativa=viagens_ativas.get(e.id),
        )
        for e in encomendas
    ]

    return itens, total


def _viagens_ativas_por_encomenda(
    db: Session,
    encomenda_ids: list[int],
) -> dict[int, ViagemAtivaResumoOut]:
    if not encomenda_ids:
        return {}

    linhas = (
        db.query(ViagemEncomenda.encomenda_id, Viagem)
        .join(Viagem, Viagem.id == ViagemEncomenda.viagem_id)
        .filter(
            ViagemEncomenda.encomenda_id.in_(encomenda_ids),
            Viagem.status.in_(STATUS_VIAGEM_ATIVOS),
        )
        .all()
    )

    return {
        encomenda_id: ViagemAtivaResumoOut(
            id=viagem.id, status=viagem.status, data_saida=viagem.data_saida
        )
        for encomenda_id, viagem in linhas
    }
