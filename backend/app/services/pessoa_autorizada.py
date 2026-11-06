from sqlalchemy.orm import Session

from app.models.destinatario import Destinatario
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.pessoa_autorizada import PessoaAutorizada

MENSAGEM_ENCOMENDA_ENTREGUE = (
    "Encomenda ja entregue: nao e possivel cadastrar pessoa autorizada."
)
MENSAGEM_TROCA_BLOQUEADA = (
    "A encomenda ja esta a retirar: nao e possivel trocar a pessoa autorizada."
)


def buscar_pessoa_autorizada(db: Session, encomenda_id: int) -> PessoaAutorizada | None:
    return (
        db.query(PessoaAutorizada)
        .filter(PessoaAutorizada.encomenda_id == encomenda_id)
        .first()
    )


def definir_pessoa_autorizada(
    db: Session,
    encomenda: Encomenda,
    nome: str,
    cpf: str,
) -> tuple[PessoaAutorizada, bool]:
    """Cadastra a pessoa autorizada da encomenda ou substitui a atual.

    Retorna (pessoa, criada). Regras:
    - encomenda entregue: nada pode ser cadastrado;
    - encomenda a_retirar: o primeiro cadastro e permitido (sem ele a retirada
      seria impossivel), mas a troca de uma pessoa ja cadastrada e bloqueada;
    - nos demais status, o cadastro substitui a pessoa anterior.
    """
    if encomenda.status == StatusEncomenda.ENTREGUE:
        raise ValueError(MENSAGEM_ENCOMENDA_ENTREGUE)

    existente = buscar_pessoa_autorizada(db, encomenda.id)

    if existente is None:
        pessoa = PessoaAutorizada(encomenda_id=encomenda.id, nome=nome, cpf=cpf)
        db.add(pessoa)
        criada = True
    else:
        if encomenda.status == StatusEncomenda.A_RETIRAR:
            raise ValueError(MENSAGEM_TROCA_BLOQUEADA)

        existente.nome = nome
        existente.cpf = cpf
        pessoa = existente
        criada = False

    db.commit()
    db.refresh(pessoa)

    return pessoa, criada


def buscar_destinatario_da_encomenda(db: Session, encomenda: Encomenda) -> Destinatario:
    return (
        db.query(Destinatario)
        .filter(Destinatario.id == encomenda.destinatario_id)
        .one()
    )
