from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate

def criar_usuario(db: Session, dados: UsuarioCreate) -> Usuario:
    usuario_existente = (
        db.query(Usuario)
        .filter(Usuario.email == dados.email)
        .first()
    )

    if usuario_existente:
        raise ValueError("E-mail já cadastrado.")

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return novo_usuario


def autenticar(
    db: Session,
    email: str,
    senha: str,
) -> Usuario | None:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == email)
        .first()
    )

    if not usuario:
        return None

    if not verificar_senha(senha, usuario.senha_hash):
        return None

    if not usuario.ativo:
        return None

    return usuario