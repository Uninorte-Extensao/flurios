from app.core.security import criar_token_acesso
from app.models.cliente import Cliente
from app.schemas.usuario import UsuarioCreate
from app.services.usuario import criar_usuario

CPF_VALIDO_1 = "12345678909"
CPF_VALIDO_2 = "98765432100"


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
        json={"cpf": CPF_VALIDO_1, "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["cpf"] == "123.***.***-09"
    assert CPF_VALIDO_1 not in response.text
    assert corpo["telefone"] == "92999990000"
    assert db_session.query(Cliente).one().cpf == CPF_VALIDO_1


def test_cadastrar_cliente_aceita_cpf_formatado_e_guarda_so_numeros(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/clientes",
        json={"cpf": "123.456.789-09", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["cpf"] == "123.***.***-09"
    assert "123.456.789-09" not in response.text
    assert db_session.query(Cliente).one().cpf == CPF_VALIDO_1


def test_cadastrar_cliente_cpf_com_digito_verificador_invalido_retorna_422(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/clientes",
        json={"cpf": "12345678900", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_cadastrar_cliente_cpf_com_todos_digitos_iguais_retorna_422(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/clientes",
        json={"cpf": "11111111111", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_cadastrar_cliente_cpf_com_tamanho_invalido_retorna_422(client, db_session):
    _, token = _cadastrar_e_logar(db_session)

    response = client.post(
        "/clientes",
        json={"cpf": "123456789", "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_cadastrar_cliente_sem_token_retorna_401(client):
    response = client.post(
        "/clientes",
        json={"cpf": CPF_VALIDO_1, "telefone": "92999990000"},
    )

    assert response.status_code == 401


def test_cadastrar_cliente_duplicado_para_mesmo_usuario(client, db_session):
    _, token = _cadastrar_e_logar(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    client.post(
        "/clientes",
        json={"cpf": CPF_VALIDO_1, "telefone": "92999990000"},
        headers=headers,
    )
    response = client.post(
        "/clientes",
        json={"cpf": CPF_VALIDO_2, "telefone": "92999990001"},
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
        json={"cpf": CPF_VALIDO_1, "telefone": "92999990000"},
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email="maria@teste.com", senha="123456"),
    )
    token_maria = criar_token_acesso({"sub": "2"})

    response = client.post(
        "/clientes",
        json={"cpf": CPF_VALIDO_1, "telefone": "92999990001"},
        headers={"Authorization": f"Bearer {token_maria}"},
    )

    assert response.status_code == 400
