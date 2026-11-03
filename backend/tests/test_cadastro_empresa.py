from app.core.security import criar_token_acesso
from app.models.empresa import PerfilEmpresa
from app.schemas.usuario import UsuarioCreate
from app.scripts.criar_admin import criar_primeiro_administrador
from app.services.empresa import completar_cadastro_empresa
from app.services.usuario import criar_usuario


def _cadastrar_administrador_logado(db_session, email="admin@teste.com"):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Admin", email=email, senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ADMINISTRADOR)
    token = criar_token_acesso({"sub": str(usuario.id)})

    return usuario, token


def test_cadastrar_empresa_sucesso(client, db_session):
    _, token_admin = _cadastrar_administrador_logado(db_session)
    criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )

    response = client.post(
        "/empresas",
        json={"email": "joao@teste.com", "perfil": "atendente"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["perfil"] == "atendente"


def test_cadastrar_empresa_sem_token_retorna_401(client, db_session):
    criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )

    response = client.post(
        "/empresas",
        json={"email": "joao@teste.com", "perfil": "atendente"},
    )

    assert response.status_code == 401


def test_cadastrar_empresa_usuario_sem_cadastro_de_empresa_retorna_403(client, db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    response = client.post(
        "/empresas",
        json={"email": "maria@teste.com", "perfil": "atendente"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_cadastrar_empresa_perfil_nao_administrador_retorna_403(client, db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Operador", email="operador@teste.com", senha="123456"),
    )
    completar_cadastro_empresa(db_session, usuario, PerfilEmpresa.ATENDENTE)
    token = criar_token_acesso({"sub": str(usuario.id)})
    criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )

    response = client.post(
        "/empresas",
        json={"email": "joao@teste.com", "perfil": "atendente"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_cadastrar_empresa_email_inexistente_retorna_404(client, db_session):
    _, token_admin = _cadastrar_administrador_logado(db_session)

    response = client.post(
        "/empresas",
        json={"email": "naoexiste@teste.com", "perfil": "atendente"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )

    assert response.status_code == 404


def test_cadastrar_empresa_usuario_ja_e_cliente_retorna_400(client, db_session):
    _, token_admin = _cadastrar_administrador_logado(db_session)
    usuario_cliente = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    token_joao = criar_token_acesso({"sub": str(usuario_cliente.id)})
    client.post(
        "/clientes",
        json={"cpf": "11122233396", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    response = client.post(
        "/empresas",
        json={"email": "joao@teste.com", "perfil": "atendente"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )

    assert response.status_code == 400


def test_criar_primeiro_administrador_sucesso(db_session):
    empresa = criar_primeiro_administrador(
        db_session, "Admin", "admin@teste.com", "senha-forte"
    )

    assert empresa.perfil == PerfilEmpresa.ADMINISTRADOR
