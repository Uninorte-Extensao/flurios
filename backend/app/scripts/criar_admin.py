"""Script de linha de comando para criar o primeiro administrador da Empresa.

Uso: python -m app.scripts.criar_admin
"""
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.empresa import Empresa, PerfilEmpresa
from app.schemas.usuario import UsuarioCreate
from app.services.empresa import completar_cadastro_empresa
from app.services.usuario import criar_usuario

def criar_primeiro_administrador(
    db: Session,
    nome: str,
    email: str,
    senha: str,
) -> Empresa:
    dados = UsuarioCreate(nome=nome, email=email, senha=senha)
    usuario = criar_usuario(db, dados)

    return completar_cadastro_empresa(db, usuario, PerfilEmpresa.ADMINISTRADOR)


def main() -> None:
    nome = input("Nome: ").strip()
    email = input("E-mail: ").strip()
    senha = getpass.getpass("Senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")

    if senha != confirmacao:
        print("As senhas nao coincidem.")
        sys.exit(1)

    db = SessionLocal()
    try:
        empresa = criar_primeiro_administrador(db, nome, email, senha)
    except (ValueError, ValidationError) as erro:
        print(f"Erro ao criar administrador: {erro}")
        sys.exit(1)
    finally:
        db.close()

    print(f"Administrador criado com sucesso (usuario_id={empresa.usuario_id}).")


if __name__ == "__main__":
    main()
