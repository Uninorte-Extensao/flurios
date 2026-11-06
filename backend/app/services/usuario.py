from sqlalchemy.orm import Session

from app.core.security import gerar_hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioMeOut
from app.services.cliente import buscar_cliente_por_usuario
from app.services.empresa import buscar_empresa_por_usuario

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


def buscar_usuario_por_email(db: Session, email: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email).first()


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


def montar_usuario_me(db: Session, usuario: Usuario) -> UsuarioMeOut:
    empresa = buscar_empresa_por_usuario(db, usuario.id)

    if empresa is not None:
        tipo, perfil = "empresa", empresa.perfil
    elif buscar_cliente_por_usuario(db, usuario.id) is not None:
        tipo, perfil = "cliente", None
    else:
        tipo, perfil = None, None

    return UsuarioMeOut(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        tipo=tipo,
        perfil=perfil,
    )
