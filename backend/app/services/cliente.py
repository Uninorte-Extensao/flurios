from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate

def completar_cadastro_cliente(
    db: Session,
    usuario: Usuario,
    dados: ClienteCreate,
) -> Cliente:
    cliente_existente = (
        db.query(Cliente)
        .filter(Cliente.usuario_id == usuario.id)
        .first()
    )

    if cliente_existente:
        raise ValueError("Usuario ja possui cadastro de cliente.")

    empresa_existente = (
        db.query(Empresa)
        .filter(Empresa.usuario_id == usuario.id)
        .first()
    )

    if empresa_existente:
        raise ValueError("Usuario ja possui cadastro de empresa.")

    cpf_em_uso = (
        db.query(Cliente)
        .filter(Cliente.cpf == dados.cpf)
        .first()
    )

    if cpf_em_uso:
        raise ValueError("CPF ja cadastrado.")

    novo_cliente = Cliente(
        usuario_id=usuario.id,
        cpf=dados.cpf,
        telefone=dados.telefone,
    )

    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)

    return novo_cliente


def buscar_cliente_por_usuario(db: Session, usuario_id: int) -> Cliente | None:
    return db.query(Cliente).filter(Cliente.usuario_id == usuario_id).first()
