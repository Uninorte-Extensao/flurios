import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.empresa import Empresa, PerfilEmpresa
from app.models.usuario import Usuario
from app.services.cliente import buscar_cliente_por_usuario
from app.services.empresa import buscar_empresa_por_usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/token")

CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Nao foi possivel validar as credenciais.",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_logado(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.PyJWTError:
        raise CREDENCIAIS_INVALIDAS

    usuario_id = payload.get("sub")

    if usuario_id is None:
        raise CREDENCIAIS_INVALIDAS

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()

    if usuario is None or not usuario.ativo:
        raise CREDENCIAIS_INVALIDAS

    return usuario


def cliente_logado(
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
) -> Cliente:
    cliente = buscar_cliente_por_usuario(db, usuario.id)

    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui cadastro de cliente.",
        )

    return cliente


def empresa_logado(
    usuario: Usuario = Depends(usuario_logado),
    db: Session = Depends(get_db),
) -> Empresa:
    empresa = buscar_empresa_por_usuario(db, usuario.id)

    if empresa is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao possui cadastro de empresa.",
        )

    return empresa


def empresa_retirada(
    empresa: Empresa = Depends(empresa_logado),
) -> Empresa:
    """Quem pode registrar retirada: funcionario do ponto de retirada e administrador."""
    if empresa.perfil not in (
        PerfilEmpresa.FUNCIONARIO_RETIRADA,
        PerfilEmpresa.ADMINISTRADOR,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acao restrita ao funcionario do ponto de retirada e a administradores.",
        )

    return empresa


def empresa_administrador(
    empresa: Empresa = Depends(empresa_logado),
) -> Empresa:
    if empresa.perfil != PerfilEmpresa.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acao restrita a administradores.",
        )

    return empresa
