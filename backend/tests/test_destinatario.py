from app.core.security import criar_token_acesso
from app.schemas.cliente import ClienteCreate
from app.schemas.usuario import UsuarioCreate
from app.services.cliente import completar_cadastro_cliente
from app.services.usuario import criar_usuario

CPF_VALIDO_1 = "11122233396"
CPF_VALIDO_2 = "22233344405"

DADOS_DESTINATARIO = {
    "nome": "Joao Pereira",
    "cpf": CPF_VALIDO_1,
    "telefone": "92988887777",
    "endereco": "Rua das Flores, 123",
    "municipio": "Tefe",
}


def _cadastrar_cliente_logado(db_session, email="maria@teste.com", cpf=CPF_VALIDO_2):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Maria", email=email, senha="123456"),
    )
    completar_cadastro_cliente(
        db_session,
        usuario,
        ClienteCreate(cpf=cpf, telefone="92999990000"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    return usuario, token


def _cadastrar_usuario_sem_cliente(db_session, email="joao@teste.com"):
    usuario = criar_usuario(
        db_session,
        UsuarioCreate(nome="Joao", email=email, senha="123456"),
    )
    token = criar_token_acesso({"sub": str(usuario.id)})

    return usuario, token


def test_cadastrar_destinatario_sucesso(client, db_session):
    _, token = _cadastrar_cliente_logado(db_session)

    response = client.post(
        "/destinatarios",
        json=DADOS_DESTINATARIO,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    corpo = response.json()
    assert corpo["nome"] == "Joao Pereira"
    assert corpo["cpf"] == CPF_VALIDO_1
    assert corpo["municipio"] == "Tefe"


def test_cadastrar_destinatario_sem_token_retorna_401(client):
    response = client.post("/destinatarios", json=DADOS_DESTINATARIO)

    assert response.status_code == 401


def test_cadastrar_destinatario_sem_cadastro_de_cliente_retorna_403(client, db_session):
    _, token = _cadastrar_usuario_sem_cliente(db_session)

    response = client.post(
        "/destinatarios",
        json=DADOS_DESTINATARIO,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_cadastrar_destinatario_permite_mesmo_cpf_em_mais_de_um_cadastro(client, db_session):
    _, token = _cadastrar_cliente_logado(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    primeira = client.post("/destinatarios", json=DADOS_DESTINATARIO, headers=headers)
    segunda = client.post("/destinatarios", json=DADOS_DESTINATARIO, headers=headers)

    assert primeira.status_code == 201
    assert segunda.status_code == 201
    assert primeira.json()["id"] != segunda.json()["id"]


def test_obter_destinatario_devolve_cpf_mascarado(client, db_session):
    _, token = _cadastrar_cliente_logado(db_session)
    headers = {"Authorization": f"Bearer {token}"}

    criado = client.post(
        "/destinatarios", json=DADOS_DESTINATARIO, headers=headers
    ).json()

    response = client.get(f"/destinatarios/{criado['id']}", headers=headers)

    assert response.status_code == 200
    corpo = response.json()
    assert corpo["cpf"] == "111.***.***-96"


def test_obter_destinatario_sem_token_retorna_401(client, db_session):
    _, token = _cadastrar_cliente_logado(db_session)
    criado = client.post(
        "/destinatarios",
        json=DADOS_DESTINATARIO,
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    response = client.get(f"/destinatarios/{criado['id']}")

    assert response.status_code == 401


def test_obter_destinatario_de_outro_cliente_retorna_404(client, db_session):
    _, token_maria = _cadastrar_cliente_logado(db_session, email="maria@teste.com", cpf=CPF_VALIDO_2)
    criado = client.post(
        "/destinatarios",
        json=DADOS_DESTINATARIO,
        headers={"Authorization": f"Bearer {token_maria}"},
    ).json()

    _, token_joao = _cadastrar_cliente_logado(db_session, email="joao@teste.com", cpf="33344455508")

    response = client.get(
        f"/destinatarios/{criado['id']}",
        headers={"Authorization": f"Bearer {token_joao}"},
    )

    assert response.status_code == 404


def test_obter_destinatario_inexistente_retorna_404(client, db_session):
    _, token = _cadastrar_cliente_logado(db_session)

    response = client.get(
        "/destinatarios/9999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
