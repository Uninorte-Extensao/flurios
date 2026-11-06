from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import cliente_logado, usuario_logado
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.pessoa_autorizada import PessoaAutorizadaCreate, PessoaAutorizadaOut
from app.services.cliente import buscar_cliente_por_usuario
from app.services.empresa import buscar_empresa_por_usuario
from app.services.encomenda import buscar_encomenda_por_id
from app.services.pessoa_autorizada import (
    buscar_destinatario_da_encomenda,
    buscar_pessoa_autorizada,
    definir_pessoa_autorizada,
)

router = APIRouter(prefix="/encomendas", tags=["pessoa-autorizada"])

NAO_ENCONTRADA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Encomenda nao encontrada.",
)


@router.post(
    "/{encomenda_id}/pessoa-autorizada",
    response_model=PessoaAutorizadaOut,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_pessoa_autorizada(
    encomenda_id: int,
    dados: PessoaAutorizadaCreate,
    response: Response,
    cliente: Cliente = Depends(cliente_logado),
    db: Session = Depends(get_db),
):
    """Cadastra (201) ou substitui (200) a pessoa autorizada. So o cliente dono."""
    encomenda = buscar_encomenda_por_id(db, encomenda_id)

    if encomenda is None or encomenda.cliente_id != cliente.id:
        raise NAO_ENCONTRADA

    if dados.destinatario_e_a_pessoa:
        if dados.nome is not None or dados.cpf is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Com destinatario_e_a_pessoa, nao informe nome nem cpf.",
            )

        destinatario = buscar_destinatario_da_encomenda(db, encomenda)
        nome, cpf = destinatario.nome, destinatario.cpf
    else:
        if dados.nome is None or not dados.nome.strip() or dados.cpf is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe nome e cpf da pessoa autorizada.",
            )

        nome, cpf = dados.nome.strip(), dados.cpf

    try:
        pessoa, criada = definir_pessoa_autorizada(db, encomenda, nome, cpf)
    except ValueError as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))

    if not criada:
        response.status_code = status.HTTP_200_OK

    return pessoa


@router.get("/{encomenda_id}/pessoa-autorizada", response_model=PessoaAutorizadaOut)
def obter_pessoa_autorizada(
    encomenda_id: int,
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
):
    """Empresa ve a de qualquer encomenda; cliente, so a das suas. CPF sempre mascarado."""
    encomenda = buscar_encomenda_por_id(db, encomenda_id)

    if encomenda is None:
        raise NAO_ENCONTRADA

    if buscar_empresa_por_usuario(db, usuario.id) is None:
        cliente = buscar_cliente_por_usuario(db, usuario.id)

        if cliente is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario sem cadastro de cliente ou empresa.",
            )

        if encomenda.cliente_id != cliente.id:
            raise NAO_ENCONTRADA

    pessoa = buscar_pessoa_autorizada(db, encomenda.id)

    if pessoa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pessoa autorizada nao cadastrada.",
        )

    return pessoa
