from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.empresa import Empresa, PerfilEmpresa
from app.models.usuario import Usuario

def buscar_empresa_por_usuario(db: Session, usuario_id: int) -> Empresa | None:
    return db.query(Empresa).filter(Empresa.usuario_id == usuario_id).first()


def completar_cadastro_empresa(
    db: Session,
    usuario: Usuario,
    perfil: PerfilEmpresa,
) -> Empresa:
    empresa_existente = buscar_empresa_por_usuario(db, usuario.id)

    if empresa_existente:
        raise ValueError("Usuario ja possui cadastro de empresa.")

    cliente_existente = (
        db.query(Cliente)
        .filter(Cliente.usuario_id == usuario.id)
        .first()
    )

    if cliente_existente:
        raise ValueError("Usuario ja possui cadastro de cliente.")

    nova_empresa = Empresa(usuario_id=usuario.id, perfil=perfil)

    db.add(nova_empresa)
    db.commit()
    db.refresh(nova_empresa)

    return nova_empresa
