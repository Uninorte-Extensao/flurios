from app.core.security import criar_token_acesso
from app.schemas.usuario import UsuarioCreate
from app.services.usuario import criar_usuario


def _cadastrar_e_logar(db_session):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    return usuario, token


def test_cadastrar_cliente_sucesso(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/clientes",
        json={"cpf": "12345678901", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["cpf"] == "12345678901"
    assert corpo["telefone"] == "92999990000"


def test_cadastrar_cliente_sem_token_retorna_401(client):
    response = client.post(
        "/clientes",
        json={"cpf": "12345678901", "telefone": "92999990000"},
    )

    assert response.status_code == 401


def test_cadastrar_cliente_duplicado_para_mesmo_usuario(client, db_session):
    _, token = _cadastrar_e_logar(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/clientes",
        json={"cpf": "12345678901", "telefone": "92999990000"},
        headers=headers,
    )
    response = client.post(
        "/clientes",
        json={"cpf": "98765432100", "telefone": "92999990001"},
        headers=headers,
    )

    assert response.status_code == 400


def test_cadastrar_cliente_cpf_duplicado_para_outro_usuario(client, db_session):
    criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email="joao@teste.com", senha="123456"),
    )
    token_joao = criar_token_acesso({"sub": "1"})

    client.post(
        "/clientes",
        json={"cpf": "12345678901", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    token_maria = criar_token_acesso({"sub": "2"})

    response = client.post(
        "/clientes",
        json={"cpf": "12345678901", "telefone": "92999990001"},
        headers={"Authorization": f"Bearer {token_maria}"},
    )

    assert response.status_code == 400
