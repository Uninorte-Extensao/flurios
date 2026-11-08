"""Prepara o banco TEMPORARIO dos testes e2e: roda as migrations e cria o administrador.

Uso (pelo rodar.mjs, com PYTHONPATH apontando para backend/):
    python preparar_banco.py <caminho-do-banco.db> <email> <senha>

Nunca usa o banco padrao (flurios.db): o caminho vem sempre por argumento.
"""
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.scripts.criar_admin import criar_primeiro_administrador

BACKEND = Path(__file__).resolve().parents[2] / "backend"


def main(caminho_banco: str, email: str, senha: str) -> None:
    url = f"sqlite:///{Path(caminho_banco).as_posix()}"

    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    engine = create_engine(url)
    sessao = sessionmaker(bind=engine)()
    try:
        criar_primeiro_administrador(sessao, "Admin Flurios", email, senha)
    finally:
        sessao.close()
        engine.dispose()


if __name__ == "__main__":
    main(*sys.argv[1:4])
