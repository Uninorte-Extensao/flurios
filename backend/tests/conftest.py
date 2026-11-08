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


def _headers_empresa_com_perfil(db_session, perfil, nome, email):
    from app.core.security import criar_token_acesso
    from app.schemas.usuario import UsuarioCreate
    from app.services.empresa import completar_cadastro_empresa
    from app.services.usuario import criar_usuario

    usuario = criar_usuario(
        db_session, UsuarioCreate(nome=nome, email=email, senha="123456")
    )
    completar_cadastro_empresa(db_session, usuario, perfil)

    return _headers(criar_token_acesso({"sub": str(usuario.id)}))


@pytest.fixture()
def headers_administrador(db_session):
    from app.models.empresa import PerfilEmpresa

    return _headers_empresa_com_perfil(
        db_session, PerfilEmpresa.ADMINISTRADOR, "Admin", "admin@teste.com"
    )


@pytest.fixture()
def headers_atendente(db_session):
    from app.models.empresa import PerfilEmpresa

    return _headers_empresa_com_perfil(
        db_session, PerfilEmpresa.ATENDENTE, "Atendente", "atendente@teste.com"
    )


@pytest.fixture()
def headers_funcionario_retirada(db_session):
    from app.models.empresa import PerfilEmpresa

    return _headers_empresa_com_perfil(
        db_session,
        PerfilEmpresa.FUNCIONARIO_RETIRADA,
        "Funcionario Retirada",
        "retirada@teste.com",
    )


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


@pytest.fixture()
def rota_com_paradas(db_session):
    """Rota Manaus -> Tefe -> Coari. `origem` e a parada de ordem 1 (Manaus);
    `destino` e uma parada valida como destino de encomenda (ordem 2)."""
    from types import SimpleNamespace

    from app.models.parada import Parada
    from app.models.rota import Rota

    rota = Rota(nome="Manaus - Coari")
    db_session.add(rota)
    db_session.flush()

    origem = Parada(rota_id=rota.id, nome="Manaus", ordem=1)
    destino = Parada(rota_id=rota.id, nome="Tefe", ordem=2)
    final = Parada(rota_id=rota.id, nome="Coari", ordem=3)
    db_session.add_all([origem, destino, final])
    db_session.commit()

    return SimpleNamespace(rota=rota, origem=origem, destino=destino, final=final)


@pytest.fixture()
def criar_encomenda_no_banco(db_session, rota_com_paradas):
    """Fabrica de encomendas gravadas direto no banco (sem passar pela API).

    Cria um cliente e um destinatario na primeira chamada e os reaproveita.
    Cada encomenda ja nasce com a movimentacao do seu status inicial.
    """
    from app.models.encomenda import Encomenda, StatusEncomenda
    from app.models.movimentacao import Movimentacao
    from app.schemas.cliente import ClienteCreate
    from app.schemas.destinatario import DestinatarioCreate
    from app.schemas.usuario import UsuarioCreate
    from app.services.cliente import completar_cadastro_cliente
    from app.services.destinatario import criar_destinatario
    from app.services.usuario import criar_usuario

    dono = {}

    def _criar(status=StatusEncomenda.PENDENTE):
        if not dono:
            usuario = criar_usuario(
                db_session,
                UsuarioCreate(nome="Dono", email="dono@teste.com", senha="123456"),
            )
            cliente = completar_cadastro_cliente(
                db_session,
                usuario,
                ClienteCreate(cpf="33344455508", telefone="92999990000"),
            )
            dono["cliente"] = cliente
            dono["destinatario"] = criar_destinatario(
                db_session,
                cliente.id,
                DestinatarioCreate(
                    nome="Joao Pereira",
                    cpf="22233344405",
                    telefone="92988887777",
                    endereco="Rua das Flores, 123",
                    municipio="Tefe",
                ),
            )

        proximo = db_session.query(Encomenda).count() + 1
        encomenda = Encomenda(
            cliente_id=dono["cliente"].id,
            destinatario_id=dono["destinatario"].id,
            parada_destino_id=rota_com_paradas.destino.id,
            codigo_rastreio=f"FLU-TESTE-{proximo:04d}",
            descricao="Caixa de ferramentas",
            status=status,
        )
        db_session.add(encomenda)
        db_session.flush()
        db_session.add(Movimentacao(encomenda_id=encomenda.id, status=status))
        db_session.commit()
        db_session.refresh(encomenda)

        return encomenda

    return _criar


@pytest.fixture()
def associar_a_viagem(client, db_session):
    """Associa pela API uma encomenda de qualquer status a uma viagem.

    A API so aceita encomendas recebidas ou aguardando embarque. Para montar
    cenarios com encomendas em outros status (embarcada, entregue...), a
    encomenda e associada como recebida e o status real e restaurado direto no
    banco, sem gerar movimentacao.
    """
    from app.models.encomenda import StatusEncomenda

    def _associar(headers, viagem_id, encomenda):
        status_real = encomenda.status
        encomenda.status = StatusEncomenda.RECEBIDA
        db_session.commit()

        resposta = client.post(
            f"/viagens/{viagem_id}/encomendas",
            json={"encomenda_id": encomenda.id},
            headers=headers,
        )
        assert resposta.status_code == 201, resposta.text

        encomenda.status = status_real
        db_session.commit()

        return resposta

    return _associar
