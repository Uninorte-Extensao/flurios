import os

os.environ.setdefault("SECRET_KEY", "chave-de-teste-nao-usar-em-producao")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def headers_empresa(db_session):
    from app.core.security import criar_token_acesso
    from app.models.empresa import PerfilEmpresa
    from app.schemas.usuario import UsuarioCreate
    from app.services.empresa import completar_cadastro_empresa
    from app.services.usuario import criar_usuario

    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Operador", email="operador@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.OPERADOR_EMBARCACAO)

    return _headers(criar_token_acesso({"sub": str(usuario.id)}))


@pytest.fixture()
def headers_cliente(db_session):
    from app.core.security import criar_token_acesso
    from app.schemas.cliente import ClienteCreate
    from app.schemas.usuario import UsuarioCreate
    from app.services.cliente import completar_cadastro_cliente
    from app.services.usuario import criar_usuario

    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    completar_cadastro_cliente(
        db_session,
        usuario,
        ClienteCreate(cpf="11122233396", telefone="92999990000"),
    )

    return _headers(criar_token_acesso({"sub": str(usuario.id)}))
