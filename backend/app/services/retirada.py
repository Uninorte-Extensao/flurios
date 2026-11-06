from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.models.encomenda import Encomenda, StatusEncomenda
from app.models.retirada import Retirada
from app.services.encomenda import atualizar_status_encomenda
from app.services.pessoa_autorizada import buscar_pessoa_autorizada

MENSAGEM_STATUS_INVALIDO = "Retirada so e permitida para encomenda a retirar."
MENSAGEM_SEM_PESSOA_AUTORIZADA = (
    "A encomenda nao tem pessoa autorizada cadastrada."
)
MENSAGEM_TERMO_NAO_ACEITO = "E obrigatorio aceitar o termo de compromisso."
MENSAGEM_CPF_NAO_CONFERE = (
    "O CPF informado nao confere com o da pessoa autorizada."
)


class TermoNaoAceitoError(Exception):
    pass


class CpfNaoConfereError(Exception):
    pass


def registrar_retirada(
    db: Session,
    encomenda: Encomenda,
    empresa: Empresa,
    cpf_retirante: str,
    termo_aceito: bool,
) -> Retirada:
    """Registra a retirada e marca a encomenda como entregue, em uma transacao.

    Levanta TermoNaoAceitoError, ValueError (status invalido / sem pessoa
    autorizada) ou CpfNaoConfereError. Nenhuma mensagem contem CPF.
    """
    if not termo_aceito:
        raise TermoNaoAceitoError(MENSAGEM_TERMO_NAO_ACEITO)

    if encomenda.status != StatusEncomenda.A_RETIRAR:
        raise ValueError(MENSAGEM_STATUS_INVALIDO)

    pessoa = buscar_pessoa_autorizada(db, encomenda.id)

    if pessoa is None:
        raise ValueError(MENSAGEM_SEM_PESSOA_AUTORIZADA)

    if pessoa.cpf != cpf_retirante:
        raise CpfNaoConfereError(MENSAGEM_CPF_NAO_CONFERE)

    retirada = Retirada(
        encomenda_id=encomenda.id,
        empresa_id=empresa.id,
        cpf_retirante=cpf_retirante,
        termo_aceito=True,
    )
    db.add(retirada)
    atualizar_status_encomenda(db, encomenda, StatusEncomenda.ENTREGUE, commit=False)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError(MENSAGEM_STATUS_INVALIDO)

    db.refresh(retirada)
    db.refresh(encomenda)

    return retirada
